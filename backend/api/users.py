"""
Users API Router.

API endpoints for user profiles and leaderboard views.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..ai_agents.orchestrator import SystemOrchestrator
from ..voting.leaderboard import LeaderboardType
from .dependencies import get_orchestrator

router = APIRouter()


class UserProfileResponse(BaseModel):
    """User profile response."""

    user_id: str
    tier: str
    level: int
    points: int
    votes_cast: int
    tokens_earned: float


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""

    rank: int
    user_id: str
    value: float
    tier: str


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get user profile."""
    stats = orchestrator.get_user_profile(user_id)
    return UserProfileResponse(
        user_id=stats["user_id"],
        tier=stats["tier"],
        level=stats["level"],
        points=stats["points"],
        votes_cast=stats["votes_cast"],
        tokens_earned=stats["tokens_earned"],
    )


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get detailed user statistics."""
    return orchestrator.get_user_profile(user_id)


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


@router.get("/{user_id}/rank")
async def get_user_rank(
    user_id: str,
    leaderboard_type: str = "points",
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get user's rank for a leaderboard type."""
    try:
        lb_type = LeaderboardType(leaderboard_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid leaderboard type")

    entry = orchestrator.leaderboard_system.get_user_rank(user_id, lb_type)
    if not entry:
        return {"rank": None, "total_users": len(orchestrator.gamification_system.user_progress)}

    return {
        "rank": entry.rank,
        "total_users": len(orchestrator.gamification_system.user_progress),
        "value": entry.value,
        "tier": entry.tier,
    }
