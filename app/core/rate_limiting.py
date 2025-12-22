"""
Rate limiting middleware for API protection.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimiter:
    """In-memory rate limiter (use Redis for production)."""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_allowed(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed based on rate limit.

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)

            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key] if req_time > window_start
            ]

            # Check limit
            if len(self.requests[key]) >= max_requests:
                oldest_request = min(self.requests[key])
                retry_after = int(
                    (
                        oldest_request + timedelta(seconds=window_seconds) - now
                    ).total_seconds()
                )
                return False, max(retry_after, 1)

            # Add current request
            self.requests[key] = [now]

            return True, 0


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Limits:
    - 100 requests per minute per IP (general)
    - 20 requests per minute for auth endpoints
    - 1000 requests per minute for authenticated users
    """

    def __init__(self, app):
        super().__init__(app)
        self.general_limit = 100
        self.auth_limit = 20
        self.user_limit = 1000
        self.window = 60  # seconds

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host

        # Determine limit based on endpoint
        path = request.url.path

        if "/auth/" in path or "/login" in path or "/register" in path:
            max_requests = self.auth_limit
            key = f"auth:{client_ip}"
        else:
            # Check if user is authenticated
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # For authenticated users, use higher limit
                # Extract user ID from token (simplified - implement proper JWT decode)
                key = f"user:{auth_header[:50]}"  # Use token prefix as key
                max_requests = self.user_limit
            else:
                max_requests = self.general_limit
                key = f"ip:{client_ip}"

        # Check rate limit
        allowed, retry_after = await rate_limiter.is_allowed(
            key, max_requests, self.window
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Window"] = str(self.window)

        return response


def get_rate_limiter():
    """Dependency to get rate limiter instance."""
    return rate_limiter
