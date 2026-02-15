"""
Database Models.

SQLAlchemy models for persisting Coliseum state.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .database import Base


class User(Base):
# ... (User model)

class KnowledgeEntry(Base):
    """Vector-backed knowledge entry for RAG."""
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    embedding: Mapped[Vector] = mapped_column(Vector(1536))  # Default for OpenAI/LiteLLM
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    """User model for authentication and progression."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    solana_address: Mapped[Optional[str]] = mapped_column(String(44), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # User progression
    points: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[str] = mapped_column(String(20), default="BRONZE")
    votes_cast: Mapped[int] = mapped_column(Integer, default=0)

    votes = relationship("Vote", back_populates="user")


class AgentModel(Base):
    """AI Agent persistence model."""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    portrait_url: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # RPG Stats
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)


class EventModel(Base):
    """Real-time event persistence model."""
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50))
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Processed results
    sentiment: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    summary: Mapped[Optional[str]] = mapped_column(Text)


class VotingSessionModel(Base):
    """Voting session persistence model."""
    __tablename__ = "voting_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    vote_type: Mapped[str] = mapped_column(String(50))
    options: Mapped[List[Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    min_stake: Mapped[float] = mapped_column(Float, default=0.0)
    reward_pool: Mapped[float] = mapped_column(Float, default=0.0)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    votes = relationship("Vote", back_populates="session")


class Vote(Base):
    """Individual vote persistence model."""
    __tablename__ = "votes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("voting_sessions.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    choice: Mapped[Any] = mapped_column(JSON)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    tokens_staked: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="votes")
    session = relationship("VotingSessionModel", back_populates="votes")
