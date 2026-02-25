"""
Voting API Router.

API endpoints for in-memory voting session lifecycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..ai_agents.orchestrator import SystemOrchestrator
from ..voting.voting_engine import VoteType
from ..models import User
from .auth import get_current_user
from .dependencies import get_orchestrator

router = APIRouter()

VOTING_ERROR_RESPONSES = {
    400: {"description": "Invalid request (invalid choice, invalid stake, or malformed payload)"},
    401: {"description": "Unauthorized"},
    404: {"description": "Voting session not found"},
    409: {"description": "Voting session inactive or duplicate vote"},
}


class CreateVotingSessionRequest(BaseModel):
    """Request to create a voting session."""

    title: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=10, max_length=2000)
    vote_type: VoteType
    options: List[str] = Field(min_length=2, max_length=20)
    duration_minutes: int = Field(default=60, gt=0, le=10080) # Max 1 week
    min_stake: float = Field(default=0.0, ge=0)


class CastVoteRequest(BaseModel):
    """Request to cast a vote."""

    choice: Any
    tokens_staked: float = Field(default=0.0, ge=0)


class VotingSessionResponse(BaseModel):
    """Voting session response model."""

    session_id: str
    title: str
    description: str
    status: str
    vote_type: str
    options: List[Any]
    total_votes: int
    starts_at: datetime
    ends_at: Optional[datetime] = None


class VoteResponse(BaseModel):
    """Vote response payload."""

    vote_id: str
    session_id: str
    user_id: str
    status: str


@router.get("/sessions", response_model=List[VotingSessionResponse])
async def list_sessions(
    status: Optional[str] = Query(default=None),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """List voting sessions, optionally filtered by status."""
    sessions = list(orchestrator.voting_engine.sessions.values())
    if status:
        sessions = [s for s in sessions if s.status.value == status]

    return [
        VotingSessionResponse(
            session_id=s.session_id,
            title=s.title,
            description=s.description,
            status=s.status.value,
            vote_type=s.vote_type.value,
            options=s.options,
            total_votes=len(s.votes),
            starts_at=s.starts_at,
            ends_at=s.ends_at,
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=VotingSessionResponse, responses=VOTING_ERROR_RESPONSES)
async def create_session(
    request: CreateVotingSessionRequest,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Create and activate a voting session."""
    if len(request.options) < 2:
        raise HTTPException(status_code=400, detail="At least two options are required")

    session = await orchestrator.create_voting_session(
        title=request.title,
        description=request.description,
        vote_type=request.vote_type,
        options=request.options,
        duration_minutes=request.duration_minutes,
        min_stake=request.min_stake,
    )

    return VotingSessionResponse(
        session_id=session.session_id,
        title=session.title,
        description=session.description,
        status=session.status.value,
        vote_type=session.vote_type.value,
        options=session.options,
        total_votes=len(session.votes),
        starts_at=session.starts_at,
        ends_at=session.ends_at,
    )


@router.post(
    "/sessions/{session_id}/vote",
    response_model=VoteResponse,
    responses=VOTING_ERROR_RESPONSES,
)
async def cast_vote(
    session_id: str,
    request: CastVoteRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Cast a vote in a session."""
    session = orchestrator.get_voting_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Voting session not found")

    if session.status.value != "active":
        raise HTTPException(status_code=409, detail="Voting session is not active")

    if request.tokens_staked < 0:
        raise HTTPException(status_code=400, detail="tokens_staked must be non-negative")

    try:
        # Map DB user_id to orchestrator string user_id
        vote = await orchestrator.cast_vote(
            session_id=session_id,
            user_id=str(current_user.id),
            choice=request.choice,
            tokens_staked=request.tokens_staked,
        )
        
        # Vote persistence is handled inside orchestrator.cast_vote() before returning.
        
    except ValueError as exc:
        detail = str(exc)
        detail_lower = detail.lower()
        if "not found" in detail_lower:
            raise HTTPException(status_code=404, detail=detail)
        if "not active" in detail_lower:
            raise HTTPException(status_code=409, detail=detail)
        if "already voted" in detail_lower:
            raise HTTPException(status_code=409, detail=detail)
        if "invalid vote choice" in detail_lower:
            raise HTTPException(status_code=400, detail=detail)
        if "insufficient stake" in detail_lower:
            raise HTTPException(status_code=400, detail=detail)
        raise HTTPException(status_code=400, detail=detail)

    return VoteResponse(
        vote_id=vote.vote_id,
        session_id=vote.session_id,
        user_id=vote.user_id,
        status="voted",
    )


@router.get("/sessions/{session_id}/results", responses=VOTING_ERROR_RESPONSES)
async def get_results(
    session_id: str,
    finalize: bool = Query(default=True),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get voting session results; finalize by default if needed."""
    session = orchestrator.get_voting_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Voting session not found")

    if finalize and session.results is None:
        try:
            await orchestrator.finalize_voting_session_durable(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "total_votes": len(session.votes),
        "results": session.results,
    }
