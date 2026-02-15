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
from ..voting.voting_engine import Vote, VoteStatus, VoteType, VotingEngine, VotingSession
from ..combat.engine import CombatEngine
from .agent import Agent
from .base_agent import AgentRole, Message
from .communication import AgentCommunicationProtocol
from .decision_engine import DecisionEngine
from .knowledge_base import KnowledgeBase
from .memory_manager import MemoryManager

from ..models import AgentModel, EventModel, Vote as VoteModel, VotingSessionModel
from ..database import AsyncSessionLocal
from sqlalchemy import select, update

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
        async with AsyncSessionLocal() as db:
            # Load Agents
            result = await db.execute(select(AgentModel))
            agent_models = result.scalars().all()
            for model in agent_models:
                if model.id not in self.agents:
                    agent = Agent(
                        role=AgentRole(model.role),
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
        async with AsyncSessionLocal() as db:
            model = AgentModel(
                id=agent.state.agent_id,
                name=agent.name,
                role=agent.state.role.value,
                is_active=agent.state.is_active,
                system_prompt=agent.system_prompt,
                last_active=agent.state.last_active,
                config=agent.state.memory,
                # Persist RPG stats from memory if available, else default
                level=agent.state.memory.get("level", 1),
                xp=agent.state.memory.get("xp", 0),
                wins=agent.state.memory.get("wins", 0),
                losses=agent.state.memory.get("losses", 0)
            )
            await db.merge(model)
            await db.commit()

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

    def create_agent(self, role: AgentRole, config: Optional[Dict[str, Any]] = None) -> Agent:
        """Create and register a new agent with shared knowledge and decision engines."""
        agent = Agent(
            role=role,
            config=config,
            knowledge_base=self.knowledge_base,
            decision_engine=self.decision_engine,
        )
        self.add_agent(agent)
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
        async with AsyncSessionLocal() as db:
            event_model = EventModel(
                id=processed.event_id,
                title=processed.title,
                description=processed.description,
                source=processed.source.value,
                category=processed.category,
                priority_score=processed.priority_score,
                timestamp=processed.timestamp,
                metadata_json=processed.metadata,
                sentiment=processed.sentiment,
                keywords=processed.keywords,
                summary=processed.summary
            )
            db.add(event_model)
            await db.commit()

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
        """List recent normalized events from ingestion history."""
        return self.ingestion_system.get_recent_events(limit=limit, source=source)

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

        # Persist to DB
        asyncio.create_task(self._persist_vote_to_db(vote))

        return vote

    async def _persist_vote_to_db(self, vote: Vote) -> None:
        """Helper to persist vote object to database."""
        async with AsyncSessionLocal() as db:
            vote_model = VoteModel(
                id=vote.vote_id,
                session_id=vote.session_id,
                user_id=int(vote.user_id),
                choice=vote.choice,
                weight=vote.weight,
                tokens_staked=vote.tokens_staked,
                timestamp=vote.timestamp
            )
            db.add(vote_model)
            await db.commit()

    def finalize_voting_session(self, session_id: str) -> Dict[str, Any]:
        """Finalize a voting session and return final results."""
        results = self.voting_engine.finalize_session(session_id)
        if results is None:
            raise ValueError("Voting session not found")
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
