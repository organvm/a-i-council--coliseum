"""
Rate Limiting Middleware

A simple in-memory rate limiter using the Fixed Window algorithm.
Prevents abuse by limiting the number of requests per client IP.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Dict, Tuple, List


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiting middleware.

    Attributes:
        limit (int): Maximum requests per window.
        window (int): Time window in seconds.
        cleanup_interval (int): How often to clean up expired entries (in requests).
    """

    def __init__(self, app, limit: int = 100, window: int = 60, cleanup_interval: int = 1000):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.cleanup_interval = cleanup_interval
        self.request_counter = 0
        # Dictionary to store client state: ip -> (window_start_time, request_count)
        self.clients: Dict[str, Tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next):
        # Extract client IP, respecting X-Forwarded-For if behind proxy
        # Note: In a real secure setup, you should only trust X-Forwarded-For from known proxies.
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()

        # Periodic cleanup to prevent memory leaks
        self.request_counter += 1
        if self.request_counter >= self.cleanup_interval:
            self._cleanup_expired_clients(now)
            self.request_counter = 0

        # Get current window state for this IP
        window_start, count = self.clients.get(client_ip, (0, 0))

        if now > window_start + self.window:
            # Start a new window
            self.clients[client_ip] = (now, 1)
        else:
            # Check if limit is exceeded
            if count >= self.limit:
                return Response(content="Too Many Requests", status_code=429)
            # Increment count
            self.clients[client_ip] = (window_start, count + 1)

        return await call_next(request)

    def _cleanup_expired_clients(self, now: float):
        """Remove clients whose window has expired."""
        expired_ips = [
            ip for ip, (start, _) in self.clients.items()
            if now > start + self.window
        ]
        for ip in expired_ips:
            del self.clients[ip]
