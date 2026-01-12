
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from backend.ai_agents.memory_manager import MemoryManager

@pytest.fixture
def memory_manager():
    return MemoryManager(max_long_term=3)

def test_lru_eviction(memory_manager):
    # Add 3 items (full capacity)
    memory_manager.add_long_term("key1", "val1")
    memory_manager.add_long_term("key2", "val2")
    memory_manager.add_long_term("key3", "val3")

    assert len(memory_manager.long_term) == 3
    assert memory_manager.get_long_term("key1") == "val1"

    # "key1" was just accessed, so it should be MRU.
    # Order: key2, key3, key1

    # Add 4th item, should trigger eviction
    memory_manager.add_long_term("key4", "val4")

    # key2 should be evicted (LRU)
    assert len(memory_manager.long_term) == 3
    assert memory_manager.get_long_term("key2") is None
    assert memory_manager.get_long_term("key1") == "val1"
    assert memory_manager.get_long_term("key3") == "val3"
    assert memory_manager.get_long_term("key4") == "val4"

def test_access_updates_lru(memory_manager):
    memory_manager.add_long_term("key1", "val1")
    memory_manager.add_long_term("key2", "val2")
    memory_manager.add_long_term("key3", "val3")
    # Order: key1, key2, key3 (LRU -> MRU)

    # Access key1, moving it to MRU
    memory_manager.get_long_term("key1")
    # Order: key2, key3, key1

    memory_manager.add_long_term("key4", "val4")
    # key2 should be evicted

    assert memory_manager.get_long_term("key2") is None
    assert memory_manager.get_long_term("key1") == "val1"

def test_ttl_expiration(memory_manager):
    # Short TTL
    # Use a fixed start time
    start_time = datetime(2023, 1, 1, 12, 0, 0)

    with patch('backend.ai_agents.memory_manager.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = start_time

        # Add item with 1 second TTL
        memory_manager.add_long_term("key1", "val1", ttl=1)

        # Add item with 1 hour TTL
        memory_manager.add_long_term("key2", "val2", ttl=3600)

        assert len(memory_manager.long_term) == 2

        # Advance time by 2 seconds
        mock_datetime.utcnow.return_value = start_time + timedelta(seconds=2)

        # Trigger cleanup by accessing or adding
        # Note: _clean_expired uses datetime.utcnow(), so it should see the new time
        val = memory_manager.get_long_term("key2")

        # key1 should be gone
        assert memory_manager.get_long_term("key1") is None
        assert memory_manager.get_long_term("key2") == "val2"
