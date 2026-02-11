"""
Events API Router.

API endpoints for event ingestion and retrieval.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..ai_agents.orchestrator import SystemOrchestrator
from ..event_pipeline.ingestion import EventSource
from .dependencies import get_orchestrator

router = APIRouter()
EVENT_ERROR_RESPONSES = {
    400: {"description": "Invalid event payload or rejected event"},
}


class IngestEventRequest(BaseModel):
    """Request to ingest an event."""

    source: EventSource
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Event response model."""

    event_id: str
    source: str
    title: str
    description: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timestamp: datetime


@router.get("/", response_model=List[EventResponse])
async def list_events(
    limit: int = Query(default=10, ge=1, le=200),
    source: Optional[EventSource] = None,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """List recent events from the in-memory event pipeline."""
    events = await orchestrator.list_events(limit=limit, source=source)

    return [
        EventResponse(
            event_id=e.event_id,
            source=e.source.value,
            title=e.title,
            description=e.description,
            category=e.category,
            tags=e.tags,
            timestamp=e.timestamp,
        )
        for e in events
    ]


@router.post("/ingest", response_model=EventResponse, responses=EVENT_ERROR_RESPONSES)
async def ingest_event(
    request: IngestEventRequest,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Ingest and process an event."""
    title = str(request.data.get("title", "")).strip()
    description = str(
        request.data.get("description")
        or request.data.get("summary")
        or request.data.get("content")
        or ""
    ).strip()
    if not title or not description:
        raise HTTPException(
            status_code=400,
            detail="Invalid event payload: 'title' and 'description' (or summary/content) are required",
        )

    event = await orchestrator.ingest_event(
        source=request.source,
        raw_data=request.data,
        metadata=request.metadata,
    )

    if not event:
        raise HTTPException(
            status_code=400,
            detail="Event rejected by filters or normalization failed",
        )

    return EventResponse(
        event_id=event.event_id,
        source=event.source.value,
        title=event.title,
        description=event.description,
        category=event.category,
        tags=event.tags,
        timestamp=event.timestamp,
    )
