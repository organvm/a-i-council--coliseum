"""
Repository Module.

Decouples database persistence logic from core orchestration systems.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal
from ..models import (
    AgentModel,
    EventModel,
    Vote as VoteModel,
    VotingSessionModel,
)
from ..ai_agents.agent import Agent
from ..voting.voting_engine import Vote
from ..event_pipeline.processing import ProcessedEvent


class SystemRepository:
    """Handles database persistence for the System Orchestrator."""

    @staticmethod
    async def load_all_agent_models() -> List[AgentModel]:
        """Load all agent models from the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AgentModel))
            return result.scalars().all()

    @staticmethod
    async def persist_agent(agent: Agent) -> None:
        """Save or update an agent in the database."""
        async with AsyncSessionLocal() as db:
            model = AgentModel(
                id=agent.state.agent_id,
                name=agent.name,
                role=agent.state.role.value,
                is_active=agent.state.is_active,
                system_prompt=agent.system_prompt,
                portrait_url=agent.state.memory.get("portrait_url"),
                last_active=agent.state.last_active,
                config=agent.state.memory,
                level=agent.state.memory.get("level", 1),
                xp=agent.state.memory.get("xp", 0),
                wins=agent.state.memory.get("wins", 0),
                losses=agent.state.memory.get("losses", 0)
            )
            await db.merge(model)
            await db.commit()

    @staticmethod
    async def persist_event(processed: ProcessedEvent) -> None:
        """Save an ingested event to the database."""
        async with AsyncSessionLocal() as db:
            metadata_json = dict(processed.metadata or {})
            if processed.tags:
                metadata_json.setdefault("tags", list(processed.tags))
            event_model = EventModel(
                id=processed.event_id,
                title=processed.title,
                description=processed.description,
                source=processed.source.value,
                category=processed.category,
                priority_score=processed.priority_score,
                timestamp=processed.timestamp,
                metadata_json=metadata_json,
                sentiment=processed.sentiment,
                keywords=processed.keywords,
                summary=processed.summary
            )
            db.add(event_model)
            await db.commit()

    @staticmethod
    async def persist_vote(vote: Vote) -> None:
        """Persist a cast vote to the database."""
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

    @staticmethod
    async def list_voting_session_models(
        *,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[VotingSessionModel]:
        """List persisted voting sessions with votes eagerly loaded."""
        async with AsyncSessionLocal() as db:
            stmt = (
                select(VotingSessionModel)
                .options(selectinload(VotingSessionModel.votes))
                .order_by(VotingSessionModel.starts_at.desc())
            )
            if status:
                stmt = stmt.where(VotingSessionModel.status == status)
            if limit is not None:
                stmt = stmt.limit(limit)
            result = await db.execute(stmt)
            return result.scalars().unique().all()

    @staticmethod
    async def get_voting_session_model(session_id: str) -> Optional[VotingSessionModel]:
        """Get one persisted voting session with votes eagerly loaded."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(VotingSessionModel)
                .options(selectinload(VotingSessionModel.votes))
                .where(VotingSessionModel.id == session_id)
            )
            return result.scalars().unique().first()

    @staticmethod
    async def load_votes_for_session(session_id: str) -> List[VoteModel]:
        """Load persisted votes for a session ordered by timestamp."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(VoteModel)
                .where(VoteModel.session_id == session_id)
                .order_by(VoteModel.timestamp.asc())
            )
            return result.scalars().all()

    @staticmethod
    async def list_event_models(
        *,
        limit: int = 10,
        source: Optional[str] = None,
    ) -> List[EventModel]:
        """List persisted events ordered by newest first."""
        async with AsyncSessionLocal() as db:
            stmt = select(EventModel).order_by(EventModel.timestamp.desc())
            if source:
                stmt = stmt.where(EventModel.source == source)
            if limit is not None:
                stmt = stmt.limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()
