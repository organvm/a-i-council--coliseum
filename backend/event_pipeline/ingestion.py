"""
Event Ingestion System

Handles incoming events from various sources and normalizes them.
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid
import asyncio
import html


class EventSource(str, Enum):
    """Sources of events"""
    RSS_FEED = "rss_feed"
    API = "api"
    WEBHOOK = "webhook"
    SOCIAL_MEDIA = "social_media"
    NEWS_API = "news_api"
    USER_SUBMISSION = "user_submission"
    BLOCKCHAIN = "blockchain"
    INTERNAL = "internal"


class RawEvent(BaseModel):
    """Raw event before processing"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: EventSource
    raw_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedEvent(BaseModel):
    """Normalized event after ingestion"""
    event_id: str
    source: EventSource
    title: str
    description: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    content: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventIngestionSystem:
    """
    System for ingesting events from various sources
    """
    
    def __init__(self):
        self.raw_events: List[RawEvent] = []
        self.normalized_events: List[NormalizedEvent] = []
        self.source_handlers: Dict[EventSource, Callable] = {}
        self.filters: List[Callable] = []
    
    def register_source_handler(
        self,
        source: EventSource,
        handler: Callable[[Dict[str, Any]], NormalizedEvent]
    ) -> None:
        """Register a handler for a specific event source"""
        self.source_handlers[source] = handler
    
    def add_filter(self, filter_func: Callable[[RawEvent], bool]) -> None:
        """Add a filter function to reject certain events"""
        self.filters.append(filter_func)
    
    async def ingest_event(
        self,
        source: EventSource,
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[NormalizedEvent]:
        """
        Ingest a raw event and normalize it
        
        Args:
            source: Source of the event
            raw_data: Raw event data
            metadata: Additional metadata
            
        Returns:
            Normalized event if accepted, None if rejected
        """
        # Create raw event
        raw_event = RawEvent(
            source=source,
            raw_data=raw_data,
            metadata=metadata or {}
        )
        
        # Apply filters
        for filter_func in self.filters:
            if not filter_func(raw_event):
                return None
        
        self.raw_events.append(raw_event)
        
        # Normalize event
        handler = self.source_handlers.get(source)
        if handler:
            normalized = handler(raw_data)
            normalized.event_id = raw_event.event_id
            normalized.source = source
            normalized.timestamp = raw_event.timestamp
        else:
            # Default normalization
            normalized = self._default_normalize(raw_event)
        
        self.normalized_events.append(normalized)
        return normalized
    
    def _default_normalize(self, raw_event: RawEvent) -> NormalizedEvent:
        """Default normalization for events without specific handler"""
        data = raw_event.raw_data

        # Sanitize inputs to prevent XSS
        title = str(data.get("title", "Untitled Event"))
        description = str(data.get("description", ""))
        content = data.get("content")

        return NormalizedEvent(
            event_id=raw_event.event_id,
            source=raw_event.source,
            title=html.escape(title),
            description=html.escape(description),
            category=data.get("category"),
            tags=data.get("tags", []),
            url=data.get("url"),
            content=html.escape(str(content)) if content is not None else None,
            timestamp=raw_event.timestamp,
            metadata=raw_event.metadata
        )
    
    async def batch_ingest(
        self,
        events: List[Dict[str, Any]],
        source: EventSource
    ) -> List[NormalizedEvent]:
        """Ingest multiple events at once"""
        tasks = [
            self.ingest_event(source, event_data)
            for event_data in events
        ]
        results = await asyncio.gather(*tasks)
        return [e for e in results if e is not None]
    
    def get_recent_events(
        self,
        limit: int = 10,
        source: Optional[EventSource] = None
    ) -> List[NormalizedEvent]:
        """Get recent normalized events - optimized to avoid full sort"""
        events = self.normalized_events
        
        # Apply source filter first, maintaining chronological order
        if source:
            events = [e for e in events if e.source == source]
        
        # Events are appended chronologically, slice the last N and reverse
        # This ensures we get the most recent N events, even after filtering
        return list(reversed(events[-limit:]))
    
    def clear_old_events(self, max_age_hours: int = 24) -> int:
        """Clear events older than specified hours"""
        cutoff = datetime.now(timezone.utc)
        cutoff = cutoff.replace(hour=cutoff.hour - max_age_hours)
        
        old_count = len(self.normalized_events)
        self.normalized_events = [
            e for e in self.normalized_events
            if e.timestamp > cutoff
        ]
        self.raw_events = [
            e for e in self.raw_events
            if e.timestamp > cutoff
        ]
        
        return old_count - len(self.normalized_events)
