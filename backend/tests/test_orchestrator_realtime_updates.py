"""Realtime emission tests for runtime (non-Director) flows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.ai_agents.orchestrator import SystemOrchestrator
from backend.event_pipeline.ingestion import EventSource
from backend.voting.voting_engine import VotePersistenceConflictError, VoteType


@pytest.mark.asyncio
async def test_runtime_vote_flow_publishes_vote_update_and_finalize_update():
    orchestrator = SystemOrchestrator()
    orchestrator.voting_engine.persist_session = AsyncMock()
    orchestrator._persist_vote_to_db = AsyncMock()

    with patch("backend.ai_agents.orchestrator.event_bus.publish", new_callable=AsyncMock) as publish_mock:
        session = await orchestrator.create_voting_session(
            title="Realtime poll",
            description="Validate runtime vote websocket emissions",
            vote_type=VoteType.MULTIPLE_CHOICE,
            options=["alpha", "beta"],
            duration_minutes=5,
        )

        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="42",
            choice="alpha",
            tokens_staked=0.0,
        )

        await orchestrator.finalize_voting_session_durable(session.session_id)

    vote_update_calls = [call for call in publish_mock.await_args_list if call.args[0] == "vote_update"]
    assert len(vote_update_calls) >= 2
    first_payload = vote_update_calls[0].args[1]
    final_payload = vote_update_calls[-1].args[1]
    assert first_payload["session_id"] == session.session_id
    assert first_payload["simulated"] is False
    assert first_payload["total_votes"] == 1
    assert final_payload["results"] is not None
    assert final_payload["status"] == "finalized"


@pytest.mark.asyncio
async def test_runtime_event_ingest_publishes_event_update():
    orchestrator = SystemOrchestrator()
    orchestrator.storage.store_event = AsyncMock()
    orchestrator.router.route_event = AsyncMock()
    orchestrator.notifications.notify_event = AsyncMock()

    with patch(
        "backend.ai_agents.orchestrator.SystemRepository.persist_event",
        new_callable=AsyncMock,
    ) as persist_event_mock, patch(
        "backend.ai_agents.orchestrator.event_bus.publish",
        new_callable=AsyncMock,
    ) as publish_mock:
        event = await orchestrator.ingest_event(
            source=EventSource.API,
            raw_data={
                "title": "Runtime event",
                "description": "Validate event_update emissions",
            },
            metadata={"channel": "test"},
        )

    assert event is not None
    persist_event_mock.assert_awaited_once()
    event_calls = [call for call in publish_mock.await_args_list if call.args[0] == "event_update"]
    assert event_calls, "expected event_update publish call"
    payload = event_calls[0].args[1]
    assert payload["event_id"] == event.event_id
    assert payload["source"] == "api"
    assert payload["title"] == "Runtime event"


@pytest.mark.asyncio
async def test_vote_persistence_conflict_rolls_back_in_memory_vote():
    orchestrator = SystemOrchestrator()
    orchestrator.voting_engine.persist_session = AsyncMock()
    orchestrator._persist_vote_to_db = AsyncMock(
        side_effect=VotePersistenceConflictError("User has already voted in this session")
    )

    session = await orchestrator.create_voting_session(
        title="Conflict poll",
        description="Rollback in-memory vote when DB rejects duplicate",
        vote_type=VoteType.MULTIPLE_CHOICE,
        options=["alpha", "beta"],
        duration_minutes=5,
    )

    with pytest.raises(ValueError, match="already voted"):
        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="99",
            choice="alpha",
            tokens_staked=0.0,
        )

    assert len(session.votes) == 0
    assert "99" not in orchestrator.voting_engine.user_votes
