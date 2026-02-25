"""
Director Mode runtime for deterministic demo sequences.

Loads simple JSON scenarios and executes timed "beats" that trigger events,
combat, chat bursts, and simulated audience voting updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..event_pipeline.ingestion import EventSource
from ..infrastructure.event_bus import event_bus
from ..voting.voting_engine import VoteStatus, VoteType, VotingSession

logger = logging.getLogger(__name__)


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class DirectorRunState:
    status: str = "idle"
    scenario: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_error: str | None = None
    run_id: str | None = None
    beat_index: int = -1
    speed_multiplier: float = 1.0
    session_aliases: dict[str, str] = field(default_factory=dict)


class DemoDirector:
    """Executes deterministic demo scenarios without replacing autonomous mode."""

    def __init__(self, orchestrator: Any, scenario_dir: str = "backend/demo/scenarios"):
        self.orchestrator = orchestrator
        self.scenario_dir = Path(scenario_dir)
        self.scenario_dir.mkdir(parents=True, exist_ok=True)
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._state = DirectorRunState()

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def list_scenarios(self) -> list[str]:
        return sorted(p.stem for p in self.scenario_dir.glob("*.json") if p.is_file())

    def status_snapshot(self) -> dict[str, Any]:
        return {
            "status": self._state.status,
            "is_running": self.is_running,
            "scenario": self._state.scenario,
            "started_at": self._state.started_at,
            "finished_at": self._state.finished_at,
            "last_error": self._state.last_error,
            "run_id": self._state.run_id,
            "beat_index": self._state.beat_index,
            "speed_multiplier": self._state.speed_multiplier,
            "session_aliases": dict(self._state.session_aliases),
            "available_scenarios": self.list_scenarios(),
        }

    async def start_scenario(
        self,
        scenario_name: str,
        *,
        restart_if_running: bool = False,
        speed_multiplier: float = 1.0,
    ) -> dict[str, Any]:
        async with self._lock:
            if self.is_running:
                if not restart_if_running:
                    raise RuntimeError("Director Mode is already running")
                await self.stop()

            if speed_multiplier <= 0:
                raise ValueError("speed_multiplier must be > 0")

            scenario = self._load_scenario(scenario_name)
            run_id = f"director-{int(datetime.utcnow().timestamp())}"
            self._state = DirectorRunState(
                status="starting",
                scenario=scenario_name,
                started_at=_utcnow_iso(),
                finished_at=None,
                last_error=None,
                run_id=run_id,
                beat_index=-1,
                speed_multiplier=speed_multiplier,
            )
            self._task = asyncio.create_task(
                self._run_scenario(scenario_name, scenario, speed_multiplier)
            )

        await self._publish_system_status("director_starting")
        return self.status_snapshot()

    async def stop(self) -> None:
        task = self._task
        self._task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self._state.status not in {"idle", "completed"}:
            self._state.status = "stopped"
            self._state.finished_at = _utcnow_iso()
            await self._publish_system_status("director_stopped")

    async def reset_runtime(self) -> dict[str, Any]:
        """Best-effort local demo reset without touching persisted DB rows."""
        await self.stop()
        self.orchestrator.combat_engine.active_battles.clear()
        self.orchestrator.voting_engine.sessions.clear()
        self.orchestrator.voting_engine.user_votes.clear()
        self._state = DirectorRunState()
        await self._publish_system_status("runtime_reset")
        return self.status_snapshot()

    def _load_scenario(self, scenario_name: str) -> dict[str, Any]:
        if "/" in scenario_name or "\\" in scenario_name or ".." in scenario_name:
            raise ValueError("Invalid scenario name")
        path = (self.scenario_dir / f"{scenario_name}.json").resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Scenario not found: {scenario_name}")
        if path.parent != self.scenario_dir.resolve():
            raise ValueError("Scenario path escape is not allowed")
        return json.loads(path.read_text(encoding="utf-8"))

    async def _run_scenario(
        self,
        scenario_name: str,
        scenario: dict[str, Any],
        speed_multiplier: float,
    ) -> None:
        self._state.status = "running"
        await self._publish_demo_marker(
            "director_intro",
            title=scenario.get("title") or scenario_name,
            subtitle=scenario.get("description", "Director Mode sequence started"),
            severity="info",
        )
        await self._publish_system_status("director_running")

        beats = scenario.get("beats") or []
        try:
            for idx, beat in enumerate(beats):
                self._state.beat_index = idx
                delay = float(beat.get("delay_seconds", 0))
                if delay > 0:
                    await asyncio.sleep(delay / speed_multiplier)
                await self._execute_beat(idx, beat)

            self._state.status = "completed"
            self._state.finished_at = _utcnow_iso()
            await self._publish_demo_marker(
                "director_complete",
                title="Sequence Complete",
                subtitle="Director Mode finished successfully",
                severity="success",
            )
            await self._publish_system_status("director_completed")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._state.status = "failed"
            self._state.last_error = str(exc)
            self._state.finished_at = _utcnow_iso()
            logger.exception("Director Mode scenario failed (%s)", scenario_name)
            await self._publish_demo_marker(
                "director_error",
                title="Director Mode Error",
                subtitle=str(exc),
                severity="error",
            )
            await self._publish_system_status("director_failed")
        finally:
            current_task = asyncio.current_task()
            if self._task is current_task:
                self._task = None

    async def _execute_beat(self, beat_index: int, beat: dict[str, Any]) -> None:
        action = str(beat.get("action", "marker"))
        payload = beat.get("payload") or {}

        if marker := beat.get("marker"):
            await self._publish_demo_marker(
                str(marker),
                title=beat.get("title") or str(marker).replace("_", " ").title(),
                subtitle=beat.get("subtitle"),
                severity=str(beat.get("severity", "info")),
            )

        if action == "marker":
            return
        if action == "ingest_event":
            await self._handle_ingest_event(payload)
            return
        if action == "start_battle":
            topic = str(payload.get("topic") or "Debate Event")
            await self.orchestrator.start_battle(topic)
            return
        if action == "chat_burst":
            await self._handle_chat_burst(payload)
            return
        if action == "create_vote_session":
            await self._handle_create_vote_session(payload)
            return
        if action == "simulate_votes":
            await self._handle_simulate_votes(payload)
            return
        if action == "finalize_vote_session":
            await self._handle_finalize_vote_session(payload)
            return
        if action == "system_status":
            await self._publish_system_status(payload.get("phase") or f"beat_{beat_index}")
            return

        raise ValueError(f"Unsupported Director Mode beat action: {action}")

    async def _handle_ingest_event(self, payload: dict[str, Any]) -> None:
        source_name = str(payload.get("source", "internal")).upper()
        source = EventSource[source_name] if source_name in EventSource.__members__ else EventSource.INTERNAL
        title = str(payload.get("title") or "Untitled Director Event")
        description = str(payload.get("description") or payload.get("summary") or "")
        metadata = payload.get("metadata") or {"director_mode": True}
        if payload.get("fast_path", True):
            normalized = await self.orchestrator.ingestion_system.ingest_event(
                source=source,
                raw_data={"title": title, "description": description, "category": payload.get("category")},
                metadata=metadata,
            )
            if normalized and payload.get("category"):
                normalized.category = str(payload["category"])
            return

        await self.orchestrator.ingest_event(
            source=source,
            raw_data={"title": title, "description": description, "category": payload.get("category")},
            metadata=metadata,
        )

    async def _handle_chat_burst(self, payload: dict[str, Any]) -> None:
        messages = payload.get("messages") or []
        interval_ms = int(payload.get("interval_ms", 250))
        for item in messages:
            if isinstance(item, str):
                user = "Audience"
                message = item
            else:
                user = str(item.get("user") or "Audience")
                message = str(item.get("message") or "")
            await event_bus.publish(
                "chat_message",
                {"user": user, "message": message, "simulated": True, "director_mode": True},
            )
            if interval_ms > 0:
                await asyncio.sleep(interval_ms / 1000)

    async def _handle_create_vote_session(self, payload: dict[str, Any]) -> None:
        vote_type_raw = str(payload.get("vote_type", "multiple_choice"))
        vote_type = VoteType(vote_type_raw)
        session = await self.orchestrator.create_voting_session(
            title=str(payload.get("title") or "Audience Poll"),
            description=str(payload.get("description") or "Synthetic audience participation demo"),
            vote_type=vote_type,
            options=list(payload.get("options") or ["A", "B"]),
            duration_minutes=int(payload.get("duration_minutes", 5)),
            min_stake=float(payload.get("min_stake", 0)),
        )
        alias = payload.get("alias")
        if alias:
            self._state.session_aliases[str(alias)] = session.session_id

        await self._publish_vote_update(session, simulated=True)

    async def _handle_simulate_votes(self, payload: dict[str, Any]) -> None:
        session = self._resolve_session(payload)
        if session is None:
            raise ValueError("simulate_votes: session not found")
        count = int(payload.get("count", 5))
        interval_ms = int(payload.get("interval_ms", 180))
        choice_sequence = payload.get("choices")

        for i in range(count):
            if session.status != VoteStatus.ACTIVE:
                break
            choice = self._choose_vote_choice(session, i, choice_sequence)
            user_id = str(int(payload.get("user_id_start", 9000)) + i)
            vote = self.orchestrator.voting_engine.cast_vote(
                session_id=session.session_id,
                user_id=user_id,
                choice=choice,
                weight=1.0,
                tokens_staked=float(payload.get("tokens_staked", 0.0)),
            )
            if vote is None:
                continue
            await self.orchestrator._persist_vote_to_db(vote)
            await self._publish_vote_update(session, simulated=True)
            if interval_ms > 0:
                await asyncio.sleep(interval_ms / 1000)

    async def _handle_finalize_vote_session(self, payload: dict[str, Any]) -> None:
        session = self._resolve_session(payload)
        if session is None:
            raise ValueError("finalize_vote_session: session not found")
        await self.orchestrator.finalize_voting_session_durable(session.session_id)
        await self._publish_vote_update(session, simulated=True)

    def _resolve_session(self, payload: dict[str, Any]) -> VotingSession | None:
        session_id = payload.get("session_id")
        session_alias = payload.get("session_alias")
        if session_alias:
            session_id = self._state.session_aliases.get(str(session_alias))
        if session_id:
            return self.orchestrator.get_voting_session(str(session_id))
        active = self.orchestrator.voting_engine.get_active_sessions()
        return active[-1] if active else None

    def _choose_vote_choice(
        self,
        session: VotingSession,
        index: int,
        choice_sequence: list[Any] | None,
    ) -> Any:
        if choice_sequence:
            return choice_sequence[index % len(choice_sequence)]
        if session.options:
            return random.choice(session.options)
        if session.vote_type == VoteType.BINARY:
            return random.choice(["yes", "no"])
        if session.vote_type == VoteType.RATING:
            return random.randint(1, 5)
        return True

    async def _publish_demo_marker(
        self,
        marker: str,
        *,
        title: str,
        subtitle: str | None = None,
        severity: str = "info",
    ) -> None:
        await event_bus.publish(
            "demo_marker",
            {
                "marker": marker,
                "title": title,
                "subtitle": subtitle,
                "severity": severity,
                "director_mode": True,
                "scenario": self._state.scenario,
                "run_id": self._state.run_id,
                "beat_index": self._state.beat_index,
                "timestamp": _utcnow_iso(),
            },
        )

    async def _publish_system_status(self, phase: str) -> None:
        await event_bus.publish(
            "system_status",
            {
                "phase": phase,
                "timestamp": _utcnow_iso(),
                "mode": "director" if self.is_running else "autonomous",
                "director_mode": self.is_running,
                "director": self.status_snapshot(),
                "orchestrator_running": bool(getattr(self.orchestrator, "is_running", False)),
            },
        )

    async def _publish_vote_update(self, session: VotingSession, *, simulated: bool) -> None:
        choice_counts: dict[str, float] = {}
        for vote in session.votes:
            key = str(vote.choice)
            choice_counts[key] = choice_counts.get(key, 0.0) + float(vote.weight)

        await event_bus.publish(
            "vote_update",
            {
                "session_id": session.session_id,
                "title": session.title,
                "status": session.status.value,
                "options": [str(opt) for opt in session.options],
                "total_votes": len(session.votes),
                "choice_weights": choice_counts,
                "results": session.results,
                "simulated": simulated,
                "director_mode": True,
                "timestamp": _utcnow_iso(),
            },
        )
