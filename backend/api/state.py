"""
State API Router.

Provides a bootstrap snapshot for frontend hydration and reconnect recovery.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request

from ..ai_agents.orchestrator import SystemOrchestrator
from ..settings import get_settings
from .dependencies import get_orchestrator

router = APIRouter()


@router.get("/bootstrap")
async def bootstrap_state(
    request: Request,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    settings = get_settings()
    events = await orchestrator.list_events(limit=10)
    sessions = list(orchestrator.voting_engine.sessions.values())
    director = getattr(request.app.state, "demo_director", None)

    return {
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "frontend_url": settings.frontend_url,
            "director_enabled": settings.demo_director_enabled,
        },
        "runtime": {
            "orchestrator_running": bool(getattr(orchestrator, "is_running", False)),
            "director": director.status_snapshot() if director else None,
        },
        "agents": [
            {
                "agent_id": a.state.agent_id,
                "name": a.name,
                "role": a.state.role.value,
                "is_active": a.state.is_active,
                "state": a.state.model_dump() if hasattr(a.state, "model_dump") else a.state.dict(),
            }
            for a in orchestrator.list_agents()
        ],
        "events": [
            {
                "event_id": e.event_id,
                "source": e.source.value,
                "title": e.title,
                "description": e.description,
                "category": e.category,
                "tags": e.tags,
                "timestamp": e.timestamp.isoformat() + "Z",
            }
            for e in events
        ],
        "voting": {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "description": s.description,
                    "status": s.status.value,
                    "vote_type": s.vote_type.value,
                    "options": s.options,
                    "total_votes": len(s.votes),
                    "starts_at": s.starts_at.isoformat() + "Z",
                    "ends_at": s.ends_at.isoformat() + "Z" if s.ends_at else None,
                    "results": s.results,
                }
                for s in sessions
            ]
        },
    }
