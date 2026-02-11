"""
Achievements API Router.

API endpoints for achievements and user completion stats.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..ai_agents.orchestrator import SystemOrchestrator
from .dependencies import get_orchestrator

router = APIRouter()


class AchievementResponse(BaseModel):
    """Achievement response model."""

    achievement_id: str
    name: str
    description: str
    tier: str
    points: int
    completed: bool = False
    progress: int = 0


@router.get("/", response_model=List[AchievementResponse])
async def list_achievements(orchestrator: SystemOrchestrator = Depends(get_orchestrator)):
    """List all achievement definitions."""
    achievements = orchestrator.achievement_system.achievements.values()
    return [
        AchievementResponse(
            achievement_id=a.achievement_id,
            name=a.name,
            description=a.description,
            tier=a.tier.value,
            points=a.points,
            completed=False,
            progress=0,
        )
        for a in achievements
    ]


@router.get("/user/{user_id}", response_model=List[AchievementResponse])
async def get_user_achievements(
    user_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get user achievements with progress."""
    achievements = orchestrator.get_user_achievements(user_id)
    return [AchievementResponse(**a) for a in achievements]


@router.get("/user/{user_id}/stats")
async def get_achievement_stats(
    user_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get user achievement completion statistics."""
    return orchestrator.achievement_system.get_completion_stats(user_id)
