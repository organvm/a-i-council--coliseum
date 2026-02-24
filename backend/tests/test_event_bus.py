import pytest
import asyncio
from backend.infrastructure.event_bus import event_bus

@pytest.mark.asyncio
async def test_event_bus_publish():
    received = []
    
    def sync_handler(event_type, data):
        received.append((event_type, data))
        
    event_bus.subscribe("test_event", sync_handler)
    
    await event_bus.publish("test_event", {"key": "value"})
    
    # Needs a small sleep to allow event loop to process Tasks
    await asyncio.sleep(0.01)
    
    assert len(received) == 1
    assert received[0] == ("test_event", {"key": "value"})
    
    event_bus.unsubscribe("test_event", sync_handler)

@pytest.mark.asyncio
async def test_event_bus_concurrent_subscribers():
    import time
    received_counts = {"count": 0}
    
    callbacks = []
    # Subscribe 100 concurrent handlers
    for i in range(100):
        async def async_handler(event_type, data, idx=i):
            received_counts["count"] += 1
        callbacks.append(async_handler)
        event_bus.subscribe("stress_test", async_handler)
        
    await event_bus.publish("stress_test", {"load": "heavy"})
    
    await asyncio.sleep(0.05)
    assert received_counts["count"] == 100
    
    # Cleanup
    for cb in callbacks:
        event_bus.unsubscribe("stress_test", cb)

@pytest.mark.asyncio
async def test_event_bus_global_subscriber():
    received = []
    
    def global_handler(event_type, data):
        received.append((event_type, data))
        
    event_bus.subscribe("*", global_handler)
    
    await event_bus.publish("any_event", {"data": "test"})
    await event_bus.publish("another_event", {"data": "test2"})
    
    await asyncio.sleep(0.01)
    
    assert len(received) == 2
    assert received[0] == ("any_event", {"data": "test"})
    assert received[1] == ("another_event", {"data": "test2"})
    
    event_bus.unsubscribe("*", global_handler)
