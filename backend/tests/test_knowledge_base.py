import pytest
from datetime import datetime, timedelta
from backend.ai_agents.knowledge_base import KnowledgeBase

@pytest.fixture
def kb():
    return KnowledgeBase()

def test_get_recent_entries_ordering(kb):
    """Test that recent entries are returned in correct order"""
    # Create entries with different timestamps
    # We need to manually set created_at because add_entry sets it to now()

    entry1 = kb.add_entry("Oldest", "test")
    entry1.created_at = datetime.utcnow() - timedelta(hours=3)

    entry2 = kb.add_entry("Newest", "test")
    entry2.created_at = datetime.utcnow()

    entry3 = kb.add_entry("Middle", "test")
    entry3.created_at = datetime.utcnow() - timedelta(hours=1)

    recent = kb.get_recent_entries(limit=3)

    assert len(recent) == 3
    assert recent[0].content == "Newest"
    assert recent[1].content == "Middle"
    assert recent[2].content == "Oldest"

def test_get_recent_entries_limit(kb):
    """Test that limit is respected"""
    for i in range(20):
        kb.add_entry(f"Entry {i}", "test")

    recent = kb.get_recent_entries(limit=5)
    assert len(recent) == 5

def test_get_recent_entries_empty(kb):
    """Test behavior with empty KB"""
    recent = kb.get_recent_entries(limit=10)
    assert recent == []

def test_get_recent_entries_fewer_than_limit(kb):
    """Test behavior when fewer entries than limit"""
    kb.add_entry("One", "test")
    recent = kb.get_recent_entries(limit=10)
    assert len(recent) == 1
    assert recent[0].content == "One"
