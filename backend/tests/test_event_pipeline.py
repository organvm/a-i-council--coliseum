"""Contract tests for event ingestion/listing and cleanup."""

from datetime import datetime, timedelta

import pytest

from backend.event_pipeline.ingestion import (
    EventIngestionSystem,
    EventSource,
    NormalizedEvent,
    RawEvent,
)


@pytest.mark.asyncio
async def test_ingest_and_list_with_source_filter():
    ingestion = EventIngestionSystem()
    await ingestion.ingest_event(
        EventSource.API,
        {"title": "API Event", "description": "from api"},
    )
    await ingestion.ingest_event(
        EventSource.USER_SUBMISSION,
        {"title": "User Event", "description": "from user"},
    )

    api_events = ingestion.get_recent_events(limit=10, source=EventSource.API)
    user_events = ingestion.get_recent_events(limit=10, source=EventSource.USER_SUBMISSION)

    assert len(api_events) == 1
    assert api_events[0].source == EventSource.API
    assert len(user_events) == 1
    assert user_events[0].source == EventSource.USER_SUBMISSION


def test_clear_old_events_boundary_conditions():
    now = datetime.utcnow()
    ingestion = EventIngestionSystem()

    keep_event = NormalizedEvent(
        event_id="newer",
        source=EventSource.API,
        title="Recent",
        description="keep",
        timestamp=now - timedelta(hours=23),
    )
    boundary_event = NormalizedEvent(
        event_id="boundary",
        source=EventSource.API,
        title="Boundary",
        description="drop",
        timestamp=now - timedelta(hours=24),
    )
    old_event = NormalizedEvent(
        event_id="older",
        source=EventSource.API,
        title="Old",
        description="drop",
        timestamp=now - timedelta(hours=25),
    )

    ingestion.normalized_events = [keep_event, boundary_event, old_event]
    ingestion.raw_events = [
        RawEvent(
            event_id="raw_newer",
            source=EventSource.API,
            raw_data={"title": "Recent"},
            timestamp=now - timedelta(hours=23),
        ),
        RawEvent(
            event_id="raw_boundary",
            source=EventSource.API,
            raw_data={"title": "Boundary"},
            timestamp=now - timedelta(hours=24),
        ),
        RawEvent(
            event_id="raw_old",
            source=EventSource.API,
            raw_data={"title": "Old"},
            timestamp=now - timedelta(hours=25),
        ),
    ]

    removed = ingestion.clear_old_events(max_age_hours=24)

    assert removed == 2
    assert [e.event_id for e in ingestion.normalized_events] == ["newer"]
    assert [e.event_id for e in ingestion.raw_events] == ["raw_newer"]

