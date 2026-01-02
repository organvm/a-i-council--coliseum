"""
Tests for Event Pipeline
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from backend.event_pipeline.ingestion import EventIngestionSystem, EventSource, NormalizedEvent
from backend.event_pipeline.prioritization import EventPrioritizer

@pytest.fixture
def ingestion_system():
    return EventIngestionSystem()

@pytest.fixture
def prioritizer():
    return EventPrioritizer()

@pytest.mark.asyncio
async def test_ingest_rss_manual(ingestion_system):
    # Simulating data passed from an RSS parser
    rss_data = {
        "title": "New AI Model Released",
        "description": "OpenAI releases GPT-5.",
        "link": "https://example.com/ai",
        "tags": ["AI", "Tech"]
    }

    event = await ingestion_system.ingest_event(EventSource.RSS_FEED, rss_data)

    assert event is not None
    assert event.source == EventSource.RSS_FEED
    assert event.title == "New AI Model Released"
    assert event.timestamp is not None

@pytest.mark.asyncio
async def test_ingest_user_submission(ingestion_system):
    user_data = {
        "title": "Community Proposal",
        "description": "Let's vote on this.",
        "user_id": "user123",
        "category": "Governance"
    }

    event = await ingestion_system.ingest_event(EventSource.USER_SUBMISSION, user_data)

    assert event is not None
    assert event.source == EventSource.USER_SUBMISSION
    assert event.metadata["user_id"] == "user123"

def test_prioritization_scoring(prioritizer):
    # High priority event (AI keyword + recent)
    event_high = NormalizedEvent(
        event_id="1",
        source=EventSource.RSS_FEED,
        title="AI Breakthrough in Medicine",
        description="Artificial Intelligence saves lives.",
        timestamp=datetime.utcnow()
    )

    # Low priority event (No keywords + old)
    event_low = NormalizedEvent(
        event_id="2",
        source=EventSource.RSS_FEED,
        title="Cat Video Viral",
        description="Funny cat jumps.",
        timestamp=datetime.utcnow() - timedelta(hours=24)
    )

    score_high = prioritizer.calculate_score(event_high)
    score_low = prioritizer.calculate_score(event_low)

    assert score_high > score_low
    # AI (0.3) + Artificial Intelligence (0.3) + Recent <1h (0.2) = 0.8 approx
    assert score_high >= 0.5

def test_prioritization_sorting(prioritizer):
    event1 = NormalizedEvent(
        event_id="1", source=EventSource.RSS_FEED,
        title="Crypto Crash", description="", timestamp=datetime.utcnow()
    )
    event2 = NormalizedEvent(
        event_id="2", source=EventSource.RSS_FEED,
        title="Boring News", description="", timestamp=datetime.utcnow()
    )

    sorted_events = prioritizer.prioritize_events([event2, event1])
    assert sorted_events[0].event_id == "1"  # Crypto keyword should boost it
