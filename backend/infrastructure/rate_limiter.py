"""Process-local sliding-window rate limiting helpers."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque, Dict


class SlidingWindowRateLimiter:
    """Simple in-process rate limiter keyed by action + actor identity."""

    def __init__(self) -> None:
        self._events: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, *, limit: int, window_seconds: float) -> bool:
        """Return True if request is allowed and record it; False otherwise."""
        now = time.monotonic()
        cutoff = now - window_seconds

        async with self._lock:
            bucket = self._events.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True

    async def clear(self) -> None:
        """Reset all recorded rate-limit windows (test helper)."""
        async with self._lock:
            self._events.clear()

    def clear_sync(self) -> None:
        """Reset windows synchronously (best-effort; intended for tests)."""
        self._events.clear()


mutation_rate_limiter = SlidingWindowRateLimiter()
