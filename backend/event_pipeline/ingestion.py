"""
Event Ingestion System

Handles incoming events from various sources and normalizes them.
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
import logging
import xml.etree.ElementTree as ET
import html

logger = logging.getLogger(__name__)

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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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

    @field_validator('title', 'description', 'content', mode='before')
    @classmethod
    def sanitize_html(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize HTML content to prevent XSS"""
        if v is None:
            return v
        return html.escape(str(v))


class EventIngestionSystem:
    """
    System for ingesting events from various sources
    """
    
    def __init__(self):
        self.raw_events: List[RawEvent] = []
        self.normalized_events: List[NormalizedEvent] = []
        self.source_handlers: Dict[EventSource, Callable] = {}
        self.filters: List[Callable] = []

        # Register default handlers
        self.register_source_handler(EventSource.RSS_FEED, self._handle_rss_feed)
        self.register_source_handler(EventSource.NEWS_API, self._handle_news_api)
        self.register_source_handler(EventSource.USER_SUBMISSION, self._handle_user_submission)
    
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
        try:
            if handler:
                normalized = handler(raw_data)
                normalized.event_id = raw_event.event_id
                normalized.source = source
                # Keep original timestamp if handler didn't set a specific one from data
                # But usually handler sets it from content. If not, use ingestion time.
                if not normalized.timestamp:
                    normalized.timestamp = raw_event.timestamp
            else:
                # Default normalization
                normalized = self._default_normalize(raw_event)

            self.normalized_events.append(normalized)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing event from {source}: {e}")
            return None
    
    def _default_normalize(self, raw_event: RawEvent) -> NormalizedEvent:
        """Default normalization for events without specific handler"""
        data = raw_event.raw_data
        return NormalizedEvent(
            event_id=raw_event.event_id,
            source=raw_event.source,
            title=data.get("title", "Untitled Event"),
            description=data.get("description", ""),
            category=data.get("category"),
            tags=data.get("tags", []),
            url=data.get("url"),
            content=data.get("content"),
            timestamp=raw_event.timestamp,
            metadata=raw_event.metadata
        )

    def _handle_rss_feed(self, data: Dict[str, Any]) -> NormalizedEvent:
        """Handle RSS feed item data"""
        # Expecting data to mimic feedparser entry or similar structure
        return NormalizedEvent(
            event_id="", # Assigned by caller
            source=EventSource.RSS_FEED,
            title=data.get("title", "No Title"),
            description=data.get("summary") or data.get("description", ""),
            url=data.get("link"),
            timestamp=datetime.utcnow(), # Parse 'published' if real RSS
            tags=data.get("tags", []),
            metadata={"author": data.get("author")}
        )

    def _handle_news_api(self, data: Dict[str, Any]) -> NormalizedEvent:
        """Handle NewsAPI article data"""
        return NormalizedEvent(
            event_id="",
            source=EventSource.NEWS_API,
            title=data.get("title", ""),
            description=data.get("description", ""),
            url=data.get("url"),
            content=data.get("content"),
            timestamp=datetime.utcnow(), # Parse 'publishedAt' if real
            metadata={"source_name": data.get("source", {}).get("name")}
        )

    def _handle_user_submission(self, data: Dict[str, Any]) -> NormalizedEvent:
        """Handle manual user submission"""
        return NormalizedEvent(
            event_id="",
            source=EventSource.USER_SUBMISSION,
            title=data.get("title", ""),
            description=data.get("description", ""),
            category=data.get("category"),
            timestamp=datetime.utcnow(),
            metadata={"user_id": data.get("user_id")}
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
        """Get recent normalized events"""
        # Bolt Optimization: Avoid full list sort/scan for recent events.
        # normalized_events is append-only, so it is naturally sorted by time.

        if limit <= 0:
            return []
        
        if source:
            # Optimized filter: iterate backwards until we find 'limit' items
            results = []
            for event in reversed(self.normalized_events):
                if event.source == source:
                    results.append(event)
                    if len(results) >= limit:
                        break
            return results

        else:
            # Optimized no-filter: slice the end and reverse
            # We want newest first, so we take the last 'limit' and reverse them
            return list(reversed(self.normalized_events[-limit:]))
    
    def clear_old_events(self, max_age_hours: int = 24) -> int:
        """Clear events older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
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
