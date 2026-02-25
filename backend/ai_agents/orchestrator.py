"""
System Orchestrator Module.

Manages AI agents and core in-memory subsystems for MVP operation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..event_pipeline.classification import EventClassifier
from ..event_pipeline.ingestion import EventIngestionSystem, EventSource, NormalizedEvent
from ..event_pipeline.notification import NotificationPriority, NotificationSystem
from ..event_pipeline.prioritization import EventPrioritizer
from ..event_pipeline.processing import EventProcessor, ProcessedEvent
from ..event_pipeline.routing import EventRouter
from ..event_pipeline.storage import EventStorage
from ..voting.achievements import AchievementSystem
from ..voting.gamification import GamificationSystem
from ..voting.leaderboard import LeaderboardSystem
from ..voting.voting_engine import (
    Vote,
    VotePersistenceConflictError,
    VoteStatus,
    VoteType,
    VotingEngine,
    VotingSession,
)
from ..combat.engine import CombatEngine
from .agent import Agent
from .base_agent import AgentRole, Message
from .communication import AgentCommunicationProtocol
from .decision_engine import DecisionEngine
from .knowledge_base import KnowledgeBase
from .memory_manager import MemoryManager

from ..infrastructure.repository import SystemRepository
from ..infrastructure.event_bus import event_bus

import random

logger = logging.getLogger(__name__)


class SystemOrchestrator:
    """Coordinates agents, event pipeline, voting, and user progression subsystems with DB persistence."""

    def __init__(self, tick_rate: float = 1.0, silence_threshold_seconds: float = 30.0):
        self.agents: Dict[str, Agent] = {}
        # ... (rest of init)

        self.tick_rate = tick_rate
        self.silence_threshold_seconds = silence_threshold_seconds
        self.last_activity_time = datetime.utcnow()

        self.is_running = False
        self.loop_task: Optional[asyncio.Task] = None
        self.communication_task: Optional[asyncio.Task] = None

        self.communication_protocol = AgentCommunicationProtocol()

        self.memory_manager = MemoryManager()
        self.knowledge_base = KnowledgeBase()
        self.decision_engine = DecisionEngine()

        self.ingestion_system = EventIngestionSystem()
        self.classifier = EventClassifier()
        self.prioritizer = EventPrioritizer()
        self.router = EventRouter()
        self.processor = EventProcessor()
        self.storage = EventStorage()
        self.notifications = NotificationSystem()

        self.processor.add_enricher("sentiment", self.processor.enrich_sentiment)
        self.processor.add_enricher("entities", self.processor.enrich_entities)
        self.processor.add_enricher("summary", self.processor.enrich_summary)
        self.processor.add_enricher("keywords", self.processor.enrich_keywords)

        self.voting_engine = VotingEngine()
        self.combat_engine = CombatEngine()
        self.gamification_system = GamificationSystem()
        self.achievement_system = AchievementSystem()
        self.leaderboard_system = LeaderboardSystem(self.gamification_system)

    async def start_battle(self, topic: str) -> str:
        """Start a combat session between two random agents."""
        if len(self.agents) < 2:
            return ""
        
        fighters = list(self.agents.keys())[:2]
        battle_id = f"battle_{int(datetime.utcnow().timestamp())}"
        
        self.combat_engine.create_battle(battle_id, topic, fighters)
        
        # Broadcast the fight start
        await self.broadcast_event(f"COMBAT STARTED: {fighters[0]} vs {fighters[1]} on '{topic}'")
        
        return battle_id

    async def load_state(self) -> None:
        """Load agents and active sessions from the database."""
        agent_models = await SystemRepository.load_all_agent_models()
        for model in agent_models:
            if model.id not in self.agents:
                # Ensure role is lowercase to match AgentRole enum values
                role_val = model.role.lower() if model.role else "observer"
                agent = Agent(
                    role=AgentRole(role_val),
                    config={**model.config, "name": model.name, "agent_id": model.id},
                    knowledge_base=self.knowledge_base,
                    decision_engine=self.decision_engine,
                )
                agent.state.is_active = model.is_active
                self.agents[model.id] = agent
                self.communication_protocol.register_agent(agent)
        
        logger.info(f"Loaded {len(agent_models)} agents from database")

        # Load Voting Sessions
        await self.voting_engine.load_active_sessions()

    async def persist_agent(self, agent: Agent) -> None:
        """Save or update an agent in the database."""
        await SystemRepository.persist_agent(agent)

    async def apply_combat_results(self, winner_id: str, loser_id: str, xp: int) -> None:
        """Update agent stats after a battle."""
        winner = self.agents.get(winner_id)
        loser = self.agents.get(loser_id)
        
        if winner:
            winner.state.memory["wins"] = winner.state.memory.get("wins", 0) + 1
            winner.state.memory["xp"] = winner.state.memory.get("xp", 0) + xp
            # Simple level up logic
            if winner.state.memory["xp"] >= winner.state.memory.get("level", 1) * 100:
                winner.state.memory["level"] = winner.state.memory.get("level", 1) + 1
                winner.state.memory["xp"] = 0
            await self.persist_agent(winner)
            
        if loser:
            loser.state.memory["losses"] = loser.state.memory.get("losses", 0) + 1
            await self.persist_agent(loser)

    def add_agent(self, agent: Agent) -> str:
        """Add/register an agent to orchestration and communication."""
        self.agents[agent.state.agent_id] = agent
        self.communication_protocol.register_agent(agent)
        return agent.state.agent_id

    def register_agent(self, agent: Agent) -> str:
        """Backward-compatible alias for add_agent."""
        return self.add_agent(agent)

    async def create_agent(self, role: AgentRole, config: Optional[Dict[str, Any]] = None) -> Agent:
        """Create and register a new agent with AI-generated visuals."""
        agent = Agent(
            role=role,
            config=config,
            knowledge_base=self.knowledge_base,
            decision_engine=self.decision_engine,
        )
        
        # Generate Generative Visual Asset
        portrait_url = await agent.nlp_processor.generate_portrait(agent.name, role.value)
        agent.state.memory["portrait_url"] = portrait_url
        
        self.add_agent(agent)
        await self.persist_agent(agent)
        return agent

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from orchestration and communication."""
        if agent_id not in self.agents:
            return False

        self.communication_protocol.unregister_agent(agent_id)
        del self.agents[agent_id]
        return True

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get one agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """List all registered agents."""
        return list(self.agents.values())

    async def start(self) -> None:
        """Start orchestrator background loops."""
        if self.is_running:
            return

        await self.load_state()
        self.is_running = True
        self.communication_task = asyncio.create_task(self.communication_protocol.start())
        self.loop_task = asyncio.create_task(self._main_loop())
        logger.info("System Orchestrator started")

    async def stop(self) -> None:
        """Stop orchestrator background loops."""
        self.is_running = False
        await self.communication_protocol.stop()

        for task in (self.loop_task, self.communication_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("System Orchestrator stopped")

    async def _main_loop(self) -> None:
        """Main periodic loop used for housekeeping and system-level tasks."""
        while self.is_running:
            try:
                await self._tick()
                await asyncio.sleep(self.tick_rate)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Error in orchestrator main loop: %s", exc)
                await asyncio.sleep(self.tick_rate)

    async def _tick(self) -> None:
        """Single orchestrator tick."""
        if not self.agents:
            return

        # 1. Progress Active Battles
        await self._run_battle_turns()
        
        # 2. Progress Autonomous Debates
        await self._run_autonomous_debates()

        # 3. Housekeeping
        now = datetime.utcnow()
# ... (rest of tick)

    async def _run_autonomous_debates(self) -> None:
        """Nudge random agents to debate the latest event."""
        if random.random() > 0.1: # Only debate ~10% of ticks to avoid spam
            return
            
        recent_events = self.ingestion_system.get_recent_events(limit=1)
        if not recent_events:
            return
            
        event = recent_events[0]
        active_agents = [a for a in self.agents.values() if a.state.is_active]
        if not active_agents:
            return
            
        speaker = random.choice(active_agents)
        
        # Construct a nudge prompt
        prompt = f"The current arena event is: {event.title}. {event.description}. What is your take?"
        
        message = Message(
            sender_id="SYSTEM_PROMPT",
            recipient_id=speaker.state.agent_id,
            content=prompt
        )
        
        response = await speaker.process_message(message)
        if response:
            await self.broadcast_message(response)
        # ... (rest of tick)

    async def _run_battle_turns(self) -> None:
        """Automatically progress all active battles."""
        for battle_id, battle in list(self.combat_engine.active_battles.items()):
            if not battle.is_active:
                continue
            
            # Identify current attacker/defender
            attacker_id = battle.turn_order[battle.current_turn_index]
            defender_id = battle.turn_order[(battle.current_turn_index + 1) % len(battle.turn_order)]
            
            # Execute one turn
            result = self.combat_engine.execute_turn(battle_id, attacker_id, defender_id)
            
            # Get names
            att_agent = self.agents.get(attacker_id)
            def_agent = self.agents.get(defender_id)
            a_name = att_agent.name if att_agent else attacker_id
            d_name = def_agent.name if def_agent else defender_id
            
            result["log"] = result["log"].replace(attacker_id, a_name).replace(defender_id, d_name)
            result["attacker_id"] = attacker_id
            result["defender_id"] = defender_id
            result["attacker_name"] = a_name
            result["defender_name"] = d_name
            
            # Broadcast the move to WebSockets for the UI
            await self.broadcast_message(Message(
                sender_id="SYSTEM_ARENA",
                content=result["log"],
                metadata={"type": "combat_update", "battle_id": battle_id, **result}
            ))

            if result["battle_over"]:
                await self.apply_combat_results(
                    result["winner"], 
                    result["loser"], 
                    result["xp_gain"]
                )
                logger.info(f"Battle {battle_id} concluded. Winner: {result['winner']}")
                
                # Close the battle
                del self.combat_engine.active_battles[battle_id]

    async def broadcast_message(self, message: Message) -> None:
        """Broadcast a Message object through the communication protocol."""
        await self.communication_protocol.send_message(message)
        ws_type = message.metadata.get("type", "agent_message") if message.metadata else "agent_message"
        await event_bus.publish(ws_type, getattr(message, "model_dump", getattr(message, "dict", lambda: {}))())
        self.last_activity_time = datetime.utcnow()

    async def broadcast_event(self, event_content: str) -> None:
        """Broadcast a plain text system event to all agents."""
        await self.communication_protocol.broadcast_message(
            sender_id="SYSTEM",
            content=event_content,
        )
        self.last_activity_time = datetime.utcnow()

    async def ingest_event(
        self,
        source: EventSource,
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProcessedEvent]:
        """Ingest, enrich, and store an event in memory."""
        event = await self.ingestion_system.ingest_event(source, raw_data, metadata)
        if not event:
            return None

        category = await self.classifier.get_primary_category(event)
        event.category = category.value

        topics = await self.classifier.extract_topics(event)
        event.tags = sorted(set(event.tags + topics))

        priority_score = self.prioritizer.calculate_score(event)

        processed = await self.processor.process_event(
            event,
            enrichments=["summary", "keywords", "sentiment", "entities"],
        )
        processed.priority_score = priority_score

        # Persist to DB
        await SystemRepository.persist_event(processed)
        logger.info(
            "Persisted event (event_id=%s source=%s category=%s priority=%.3f)",
            processed.event_id,
            processed.source.value,
            processed.category,
            float(processed.priority_score or 0.0),
        )

        await event_bus.publish(
            "event_update",
            {
                "event_id": processed.event_id,
                "source": processed.source.value,
                "title": processed.title,
                "description": processed.description,
                "category": processed.category,
                "tags": list(processed.tags),
                "timestamp": processed.timestamp.isoformat() + "Z",
            },
        )

        await self.storage.store_event(processed)
        await self.router.route_event(event, priority_score=priority_score)

        notification_priority = self._notification_priority_from_score(priority_score)
        await self.notifications.notify_event(processed, priority=notification_priority)

        return processed

    async def list_events(
        self,
        limit: int = 10,
        source: Optional[EventSource] = None,
    ) -> List[NormalizedEvent]:
        """List recent normalized events from persisted storage."""
        models = await SystemRepository.list_event_models(
            limit=limit,
            source=source.value if source else None,
        )
        events: List[NormalizedEvent] = []
        for model in models:
            try:
                event_source = EventSource(model.source)
            except ValueError:
                logger.warning(
                    "Unknown persisted event source '%s' for event_id=%s; defaulting to internal",
                    model.source,
                    model.id,
                )
                event_source = EventSource.INTERNAL

            metadata = dict(model.metadata_json or {})
            tags = metadata.get("tags")
            if not isinstance(tags, list):
                tags = list(model.keywords or [])

            events.append(
                NormalizedEvent(
                    event_id=model.id,
                    source=event_source,
                    title=model.title,
                    description=model.description,
                    category=model.category,
                    tags=[str(tag) for tag in tags],
                    timestamp=model.timestamp,
                    metadata=metadata,
                )
            )
        return events

    async def list_voting_sessions_snapshot(
        self,
        *,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[VotingSession]:
        """Read persisted voting sessions as detached snapshots for API/bootstrap responses."""
        models = await SystemRepository.list_voting_session_models(status=status, limit=limit)
        return self.voting_engine.snapshot_from_models(models)

    async def get_voting_session_snapshot(self, session_id: str) -> Optional[VotingSession]:
        """Read one persisted voting session snapshot for API responses."""
        model = await SystemRepository.get_voting_session_model(session_id)
        return self.voting_engine.snapshot_one_from_model(model)

    async def create_voting_session(
        self,
        title: str,
        description: str,
        vote_type: VoteType,
        options: List[Any],
        duration_minutes: int = 60,
        min_stake: float = 0.0,
    ) -> VotingSession:
        """Create and activate a voting session."""
        session = await self.voting_engine.create_session(
            title=title,
            description=description,
            vote_type=vote_type,
            options=options,
            duration_minutes=duration_minutes,
            min_stake=min_stake,
        )
        await self.voting_engine.start_session(session.session_id)
        return session

    async def cast_vote(
        self,
        session_id: str,
        user_id: str,
        choice: Any,
        tokens_staked: float = 0.0,
    ) -> Vote:
        """Cast a weighted vote and update user progression."""
        session = self.voting_engine.sessions.get(session_id)
        if not session:
            raise ValueError("Voting session not found")
        if session.status != VoteStatus.ACTIVE:
            raise ValueError("Voting session is not active")
        if session.ends_at and datetime.utcnow() > session.ends_at:
            self.voting_engine.close_session(session_id)
            await self.voting_engine.persist_session(session)
            raise ValueError("Voting session is not active")
        if tokens_staked < session.min_stake:
            raise ValueError("Insufficient stake for this session")
        if any(v.user_id == user_id for v in session.votes):
            raise ValueError("User has already voted in this session")
        if not self._is_valid_vote_choice(session, choice):
            raise ValueError("Invalid vote choice")

        user_progress = self.gamification_system.get_or_create_user_progress(user_id)
        vote_weight = self.gamification_system.get_tier_benefits(user_progress.tier)["vote_weight"]

        vote = self.voting_engine.cast_vote(
            session_id=session_id,
            user_id=user_id,
            choice=choice,
            weight=vote_weight,
            tokens_staked=tokens_staked,
        )
        if vote is None:
            raise ValueError("Vote rejected")

        updated_progress = self.gamification_system.record_vote(user_id)
        votes_cast = updated_progress.votes_cast
        self.achievement_system.track_progress(user_id, "first_vote", votes_cast)
        self.achievement_system.track_progress(user_id, "voting_veteran", votes_cast)
        self.achievement_system.track_progress(user_id, "democratic_champion", votes_cast)

        # Persist before returning so API responses reflect durable state.
        try:
            await self._persist_vote_to_db(vote)
        except VotePersistenceConflictError:
            self.voting_engine.discard_vote_from_memory(vote)
            logger.warning(
                "Duplicate vote rejected by DB constraint (session_id=%s user_id=%s)",
                session_id,
                user_id,
            )
            raise ValueError("User has already voted in this session")
        except Exception:
            self.voting_engine.discard_vote_from_memory(vote)
            logger.exception(
                "Vote persistence failed after in-memory cast (session_id=%s user_id=%s)",
                session_id,
                user_id,
            )
            raise

        await event_bus.publish("vote_update", self._serialize_vote_update(session, simulated=False))
        logger.info(
            "Vote persisted (session_id=%s user_id=%s total_votes=%s status=%s)",
            session_id,
            user_id,
            len(session.votes),
            session.status.value,
        )

        return vote

    async def _persist_vote_to_db(self, vote: Vote) -> None:
        """Helper to persist vote object to database."""
        await self.voting_engine.persist_vote(vote)

    def finalize_voting_session(self, session_id: str) -> Dict[str, Any]:
        """Finalize a voting session and return final results."""
        results = self.voting_engine.finalize_session(session_id)
        if results is None:
            raise ValueError("Voting session not found")
        return results

    async def finalize_voting_session_durable(self, session_id: str) -> Dict[str, Any]:
        """Finalize and persist session status/results for restart consistency."""
        results = await self.voting_engine.finalize_session_and_persist(session_id)
        if results is None:
            raise ValueError("Voting session not found")
        session = self.voting_engine.sessions.get(session_id)
        if session is not None:
            await event_bus.publish("vote_update", self._serialize_vote_update(session, simulated=False))
            logger.info(
                "Voting session finalized (session_id=%s total_votes=%s)",
                session_id,
                len(session.votes),
            )
        return results

    def get_voting_session(self, session_id: str) -> Optional[VotingSession]:
        """Get voting session by ID."""
        return self.voting_engine.sessions.get(session_id)

    def get_voting_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get finalized results for a session."""
        session = self.voting_engine.sessions.get(session_id)
        if not session:
            return None
        return session.results

    @staticmethod
    def _is_valid_vote_choice(session: VotingSession, choice: Any) -> bool:
        """Validate vote choice against session vote type/options."""
        if session.vote_type == VoteType.BINARY:
            allowed = {True, False, 1, 0, "yes", "no", "agree", "disagree", "Yes", "No"}
            return choice in allowed
        if session.vote_type == VoteType.MULTIPLE_CHOICE:
            return choice in session.options
        if session.vote_type == VoteType.RANKED:
            if not isinstance(choice, list) or not choice:
                return False
            return set(choice).issubset(set(session.options))
        if session.vote_type == VoteType.RATING:
            if not isinstance(choice, (int, float)):
                return False
            return 1 <= float(choice) <= 5
        return True

    @staticmethod
    def _serialize_vote_update(session: VotingSession, *, simulated: bool) -> Dict[str, Any]:
        """Create a UI-friendly vote update payload shared across runtime and demo modes."""
        choice_counts: Dict[str, float] = {}
        for vote in session.votes:
            key = str(vote.choice)
            choice_counts[key] = choice_counts.get(key, 0.0) + float(vote.weight)

        return {
            "session_id": session.session_id,
            "title": session.title,
            "status": session.status.value,
            "options": [str(opt) for opt in session.options],
            "total_votes": len(session.votes),
            "choice_weights": choice_counts,
            "results": session.results,
            "simulated": simulated,
            "director_mode": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile and progression stats."""
        return self.gamification_system.get_user_stats(user_id)

    def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get expanded achievement objects for a user."""
        user_achievements = self.achievement_system.get_user_achievements(user_id)
        expanded: List[Dict[str, Any]] = []
        for ua in user_achievements:
            definition = self.achievement_system.get_achievement(ua.achievement_id)
            if not definition:
                continue
            expanded.append(
                {
                    "achievement_id": definition.achievement_id,
                    "name": definition.name,
                    "description": definition.description,
                    "tier": definition.tier.value,
                    "points": definition.points,
                    "completed": ua.completed,
                    "progress": ua.progress,
                }
            )
        return expanded

    @staticmethod
    def _notification_priority_from_score(score: float) -> NotificationPriority:
        if score >= 2.0:
            return NotificationPriority.URGENT
        if score >= 1.0:
            return NotificationPriority.HIGH
        if score >= 0.5:
            return NotificationPriority.MEDIUM
        return NotificationPriority.LOW
