"""
Voting Engine Module

Handles viewer voting on council debates and decisions.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class VoteType(str, Enum):
    """Types of votes"""
    BINARY = "binary"  # Agree/Disagree
    MULTIPLE_CHOICE = "multiple_choice"
    RANKED = "ranked"
    RATING = "rating"  # 1-5 stars


class VoteStatus(str, Enum):
    """Status of voting session"""
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    FINALIZED = "finalized"


class Vote(BaseModel):
    """Individual vote from a user"""
    vote_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    choice: Any
    weight: float = 1.0
    tokens_staked: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VotingSession(BaseModel):
    """A voting session on a topic"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    vote_type: VoteType
    options: List[Any]
    status: VoteStatus = VoteStatus.PENDING
    starts_at: datetime = Field(default_factory=datetime.utcnow)
    ends_at: Optional[datetime] = None
    duration_minutes: int = 60
    votes: List[Vote] = Field(default_factory=list)
    results: Optional[Dict[str, Any]] = None
    min_stake: float = 0.0  # Minimum tokens to vote
    reward_pool: float = 0.0  # Tokens distributed to voters
    created_at: datetime = Field(default_factory=datetime.utcnow)


from ..database import AsyncSessionLocal
from ..models import VotingSessionModel, Vote as VoteModel
from sqlalchemy import select, update
import asyncio
import logging

logger = logging.getLogger(__name__)

class VotingEngine:
    """
    Engine for managing viewer voting sessions with DB persistence
    """
    
    def __init__(self):
        # We still keep a small cache for speed, but primary source is DB
        self.sessions: Dict[str, VotingSession] = {}
        self.user_votes: Dict[str, List[str]] = {}

    async def load_active_sessions(self) -> None:
        """Hydrate the in-memory engine from the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(VotingSessionModel).where(VotingSessionModel.status == "active")
            )
            models = result.scalars().all()
            for m in models:
                session = VotingSession(
                    session_id=m.id,
                    title=m.title,
                    description=m.description,
                    vote_type=VoteType(m.vote_type),
                    options=m.options,
                    status=VoteStatus(m.status),
                    starts_at=m.starts_at,
                    ends_at=m.ends_at,
                    min_stake=m.min_stake,
                    reward_pool=m.reward_pool,
                    results=m.results
                )
                self.sessions[session.session_id] = session
            logger.info(f"Hydrated {len(models)} active voting sessions")

    async def persist_session(self, session: VotingSession) -> None:
        """Save session state to DB."""
        async with AsyncSessionLocal() as db:
            model = VotingSessionModel(
                id=session.session_id,
                title=session.title,
                description=session.description,
                vote_type=session.vote_type.value,
                options=session.options,
                status=session.status.value,
                starts_at=session.starts_at,
                ends_at=session.ends_at,
                min_stake=session.min_stake,
                reward_pool=session.reward_pool,
                results=session.results
            )
            await db.merge(model)
            await db.commit()
    
    async def create_session(
        self,
        title: str,
        description: str,
        vote_type: VoteType,
        options: List[Any],
        duration_minutes: int = 60,
        min_stake: float = 0.0,
        reward_pool: float = 0.0
    ) -> VotingSession:
        session = VotingSession(
            title=title,
            description=description,
            vote_type=vote_type,
            options=options,
            duration_minutes=duration_minutes,
            min_stake=min_stake,
            reward_pool=reward_pool
        )
        
        session.ends_at = session.starts_at + timedelta(minutes=duration_minutes)
        
        self.sessions[session.session_id] = session
        await self.persist_session(session)
        return session
    
    async def start_session(self, session_id: str) -> bool:
        """Start a voting session"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.status = VoteStatus.ACTIVE
        session.starts_at = datetime.utcnow()
        session.ends_at = session.starts_at + timedelta(minutes=session.duration_minutes)
        await self.persist_session(session)
        return True
    
    def cast_vote(
        self,
        session_id: str,
        user_id: str,
        choice: Any,
        weight: float = 1.0,
        tokens_staked: float = 0.0
    ) -> Optional[Vote]:
        """
        Cast a vote in a session
        
        Args:
            session_id: Session to vote in
            user_id: User casting vote
            choice: Vote choice
            weight: Vote weight (based on stake)
            tokens_staked: Tokens staked for this vote
            
        Returns:
            Vote if successful, None otherwise
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if session.status != VoteStatus.ACTIVE:
            return None
        
        # Check if session has ended
        if session.ends_at and datetime.utcnow() > session.ends_at:
            self.close_session(session_id)
            return None
        
        # Check minimum stake
        if tokens_staked < session.min_stake:
            return None
        
        # Check if user already voted
        existing_vote = next(
            (v for v in session.votes if v.user_id == user_id),
            None
        )
        if existing_vote:
            return None
        
        # Create vote
        vote = Vote(
            session_id=session_id,
            user_id=user_id,
            choice=choice,
            weight=weight,
            tokens_staked=tokens_staked
        )
        
        session.votes.append(vote)
        
        # Track user votes
        if user_id not in self.user_votes:
            self.user_votes[user_id] = []
        self.user_votes[user_id].append(vote.vote_id)
        
        return vote
    
    def close_session(self, session_id: str) -> bool:
        """Close a voting session"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.status = VoteStatus.CLOSED
        return True
    
    def finalize_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Finalize session and calculate results
        
        Returns:
            Results dictionary
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if session.status != VoteStatus.CLOSED:
            self.close_session(session_id)
        
        # Calculate results based on vote type
        if session.vote_type == VoteType.BINARY:
            results = self._calculate_binary_results(session)
        elif session.vote_type == VoteType.MULTIPLE_CHOICE:
            results = self._calculate_multiple_choice_results(session)
        elif session.vote_type == VoteType.RANKED:
            results = self._calculate_ranked_results(session)
        elif session.vote_type == VoteType.RATING:
            results = self._calculate_rating_results(session)
        else:
            results = {}
        
        session.results = results
        session.status = VoteStatus.FINALIZED
        
        return results
    
    def _calculate_binary_results(self, session: VotingSession) -> Dict[str, Any]:
        """Calculate binary vote results"""
        yes_votes = sum(
            v.weight for v in session.votes
            if v.choice in [True, "yes", "Yes", 1, "agree"]
        )
        no_votes = sum(
            v.weight for v in session.votes
            if v.choice in [False, "no", "No", 0, "disagree"]
        )
        
        total = yes_votes + no_votes
        
        return {
            "yes": yes_votes,
            "no": no_votes,
            "total_votes": len(session.votes),
            "yes_percentage": (yes_votes / total * 100) if total > 0 else 0,
            "no_percentage": (no_votes / total * 100) if total > 0 else 0,
            "winner": "yes" if yes_votes > no_votes else "no"
        }
    
    def _calculate_multiple_choice_results(self, session: VotingSession) -> Dict[str, Any]:
        """Calculate multiple choice results"""
        choice_weights: Dict[Any, float] = {}
        
        for vote in session.votes:
            if vote.choice not in choice_weights:
                choice_weights[vote.choice] = 0
            choice_weights[vote.choice] += vote.weight
        
        total = sum(choice_weights.values())
        
        results = {
            "choices": choice_weights,
            "total_votes": len(session.votes),
            "percentages": {
                choice: (weight / total * 100) if total > 0 else 0
                for choice, weight in choice_weights.items()
            }
        }
        
        if choice_weights:
            results["winner"] = max(choice_weights.items(), key=lambda x: x[1])[0]
        
        return results
    
    def _calculate_ranked_results(self, session: VotingSession) -> Dict[str, Any]:
        """Calculate ranked choice results"""
        # Simplified ranked choice implementation
        choice_scores: Dict[Any, float] = {}
        
        for vote in session.votes:
            if isinstance(vote.choice, list):
                for rank, choice in enumerate(vote.choice):
                    if choice not in choice_scores:
                        choice_scores[choice] = 0
                    # Higher ranks get more points
                    choice_scores[choice] += vote.weight * (len(vote.choice) - rank)
        
        sorted_choices = sorted(
            choice_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "rankings": sorted_choices,
            "total_votes": len(session.votes),
            "winner": sorted_choices[0][0] if sorted_choices else None
        }
    
    def _calculate_rating_results(self, session: VotingSession) -> Dict[str, Any]:
        """Calculate rating results"""
        ratings: List[float] = []
        
        for vote in session.votes:
            if isinstance(vote.choice, (int, float)):
                ratings.append(float(vote.choice) * vote.weight)
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "average_rating": avg_rating,
            "total_votes": len(session.votes),
            "rating_distribution": {
                i: sum(1 for r in ratings if int(r) == i)
                for i in range(1, 6)
            }
        }
    
    def get_user_votes(self, user_id: str) -> List[Vote]:
        """Get all votes by a user"""
        vote_ids = self.user_votes.get(user_id, [])
        votes = []
        
        for session in self.sessions.values():
            for vote in session.votes:
                if vote.vote_id in vote_ids:
                    votes.append(vote)
        
        return votes
    
    def get_active_sessions(self) -> List[VotingSession]:
        """Get all active voting sessions"""
        return [
            s for s in self.sessions.values()
            if s.status == VoteStatus.ACTIVE
        ]
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        total_stake = sum(v.tokens_staked for v in session.votes)
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "status": session.status.value,
            "total_votes": len(session.votes),
            "total_stake": total_stake,
            "participation_rate": len(set(v.user_id for v in session.votes)),
            "time_remaining": (
                (session.ends_at - datetime.utcnow()).total_seconds()
                if session.ends_at and session.ends_at > datetime.utcnow()
                else 0
            )
        }
