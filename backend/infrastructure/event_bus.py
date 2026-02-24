"""
Event Bus Infrastructure Module.

Provides an async pub/sub bus to decouple the orchestrator from websockets and other systems.
Supports both in-memory (for tests/local dev) and Redis (for distributed environments).
"""

import asyncio
import logging
import json
import os
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

class EventBus:
    """Async Pub/Sub system for internal application events."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self.use_redis = os.getenv("USE_REDIS", "false").lower() == "true"
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = None
        self.pubsub = None
        self._listener_task = None

    async def start(self):
        """Start the EventBus (connects to Redis if enabled)."""
        if self.use_redis:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                self.pubsub = self.redis.pubsub()
                await self.pubsub.subscribe("coliseum_events")
                self._listener_task = asyncio.create_task(self._listen_redis())
                logger.info("EventBus connected to Redis.")
            except Exception as e:
                logger.error(f"Failed to connect EventBus to Redis: {e}. Falling back to in-memory.")
                self.use_redis = False

    async def stop(self):
        """Stop the EventBus."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
            
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe a callback to an event type. Use '*' for all events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe a callback from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers or to Redis."""
        if self.use_redis and self.redis:
            try:
                payload = json.dumps({"event_type": event_type, "data": data})
                await self.redis.publish("coliseum_events", payload)
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")
                # Fallback to local
                await self._dispatch_local(event_type, data)
        else:
            await self._dispatch_local(event_type, data)

    async def _listen_redis(self):
        """Listen for messages from Redis and dispatch them locally."""
        if not self.pubsub:
            return
            
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        event_type = payload.get("event_type")
                        data = payload.get("data")
                        await self._dispatch_local(event_type, data)
                    except Exception as e:
                        logger.error(f"Failed to parse Redis message: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener loop ended with error: {e}")

    async def _dispatch_local(self, event_type: str, data: Any = None) -> None:
        """Dispatch an event to local memory subscribers."""
        callbacks = self._subscribers.get(event_type, [])[:]
        # Also run global subscribers
        callbacks.extend(self._subscribers.get("*", []))
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event_type, data))
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event bus subscriber for {event_type}: {e}")

# Global singleton event bus
event_bus = EventBus()
