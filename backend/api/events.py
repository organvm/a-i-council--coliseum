"""
Events API Router

API endpoints for event management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..ai_agents.orchestrator import SystemOrchestrator
from .dependencies import get_orchestrator
from ..event_pipeline.ingestion import EventSource

router = APIRouter()


class IngestEventRequest(BaseModel):
    """Request to ingest an event"""
    source: EventSource
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Event response model"""
    event_id: str
    source: str
    title: str
    description: str
    category: Optional[str] = None
    timestamp: str


@router.get("/", response_model=List[EventResponse])
async def list_events(
    limit: int = 10,
    source: Optional[EventSource] = None,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """List recent events from the pipeline"""
    events = orchestrator.event_system.get_recent_events(limit, source)

    return [
        EventResponse(
            event_id=e.event_id,
            source=e.source,
            title=e.title,
            description=e.description,
            category=e.category,
            timestamp=e.timestamp.isoformat()
        )
        for e in events
    ]


@router.post("/ingest", response_model=EventResponse)
async def ingest_event(
    request: IngestEventRequest,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Ingest a new event manually"""
    event = await orchestrator.event_system.ingest_event(
        source=request.source,
        raw_data=request.data,
        metadata=request.metadata
    )

    if not event:
        raise HTTPException(status_code=400, detail="Event rejected by filters or handler failed")

    return EventResponse(
        event_id=event.event_id,
        source=event.source,
        title=event.title,
        description=event.description,
        category=event.category,
        timestamp=event.timestamp.isoformat()
    )
