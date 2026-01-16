"""
Rate Limit Middleware

A simple in-memory rate limiter middleware for FastAPI.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the number of requests per IP address within a time window.

    Attributes:
        requests_per_minute (int): Maximum number of requests allowed per minute.
        request_counts (dict): Dictionary to store request counts per IP.
                               Key: IP address (str)
                               Value: (count, reset_time)
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for websocket connections
        if request.scope["type"] == "websocket":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Periodic cleanup (lazy) to prevent memory leaks
        # If dictionary grows too large (>10000 IPs), clear it.
        # This is a simple strategy; for production, use Redis or similar.
        if len(self.request_counts) > 10000:
            self.request_counts.clear()

        # Initialize or get current count for IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = (0, current_time + 60)

        count, reset_time = self.request_counts[client_ip]

        # Reset window if time passed
        if current_time > reset_time:
            self.request_counts[client_ip] = (1, current_time + 60)
        else:
            # Check limit
            if count >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )
            self.request_counts[client_ip] = (count + 1, reset_time)

        response = await call_next(request)
        return response
