"""
Users API Router.

API endpoints for user authentication, profiles and leaderboard views.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai_agents.orchestrator import SystemOrchestrator
from ..database import get_db
from ..models import User
from ..voting.leaderboard import LeaderboardType
from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,  # allow-secret
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from .dependencies import get_orchestrator

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # allow-secret


class Token(BaseModel):
    access_token: str
    token_type: str


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: int
    username: str
    email: str
    tier: str
    points: int
    votes_cast: int
    solana_address: Optional[str] = None


class LinkSolanaRequest(BaseModel):
    solana_address: str


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""

    rank: int
    user_id: str
    value: float
    tier: str


@router.post("/register", response_model=UserProfileResponse)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    result = await db.execute(
        select(User).where((User.username == user_in.username) | (User.email == user_in.email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )
    
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login to get access token."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserProfileResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.post("/link-solana", response_model=UserProfileResponse)
async def link_solana(
    request: LinkSolanaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a Solana wallet to the user account."""
    current_user.solana_address = request.solana_address
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/refresh-tier", response_model=UserProfileResponse)
async def refresh_tier(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh user tier based on on-chain balance."""
    if not current_user.solana_address:
        raise HTTPException(status_code=400, detail="Solana address not linked")
    
    from ..blockchain.solana_contracts import SolanaContractManager
    manager = SolanaContractManager()
    
    new_tier = await manager.verify_stake_tier(current_user.solana_address)
    current_user.tier = new_tier
    
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get user profile by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/leaderboard/{leaderboard_type}", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    leaderboard_type: str,
    limit: int = 100,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get leaderboard by type."""
    try:
        lb_type = LeaderboardType(leaderboard_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid leaderboard type")

    # Note: Leaderboard currently uses in-memory gamification system
    entries = orchestrator.leaderboard_system.get_top_users(lb_type, limit=limit)
    return [
        LeaderboardEntry(
            rank=e.rank,
            user_id=e.user_id,
            value=e.value,
            tier=e.tier or "bronze",
        )
        for e in entries
    ]
