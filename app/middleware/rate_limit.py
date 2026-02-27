"""
Rate limiting middleware using slowapi
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings

# Initialize rate limiter
# Use memory storage by default unless a real external Redis host is configured.
# This prevents 500 errors in environments without Redis (like App Runner).
use_redis = bool(settings.REDIS_HOST and settings.REDIS_HOST != "localhost")

redis_uri = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}" if settings.REDIS_PASSWORD else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"],  # Global default
    storage_uri=redis_uri if use_redis else "memory://",
    strategy="fixed-window",
)


def get_rate_limit_key(request: Request) -> str:
    """
    Custom rate limit key function
    Uses user ID if authenticated, otherwise IP address
    """
    # Check if user is authenticated
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Rate limit tiers for different endpoint types
RATE_LIMITS = {
    "auth": "5/minute",  # Authentication endpoints
    "api_read": "100/minute",  # Read operations
    "api_write": "30/minute",  # Write operations
    "public": "20/minute",  # Public endpoints
    "websocket": "10/minute",  # WebSocket connections
}
