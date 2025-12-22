"""
Rate limiting middleware using slowapi
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour"],  # Global default
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    if settings.REDIS_HOST
    else "memory://",
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
