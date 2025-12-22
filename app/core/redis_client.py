"""
Redis Configuration and Client Setup
Provides Redis connection for caching, sessions, and real-time features
"""

import redis
from redis import Redis
from typing import Optional
import os
import json
from functools import wraps


class RedisClient:
    """Singleton Redis client for the application"""

    _instance: Optional[Redis] = None

    @classmethod
    def get_instance(cls) -> Redis:
        """Get or create Redis instance"""
        if cls._instance is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            cls._instance = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return cls._instance

    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None


# Cache decorator for functions
def cache_result(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache function results in Redis

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache keys
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]

            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))

            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")

            cache_key = ":".join(key_parts)

            # Try to get from cache
            redis_client = RedisClient.get_instance()
            cached = redis_client.get(cache_key)

            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result

        return wrapper

    return decorator


class SessionManager:
    """Manage user sessions in Redis"""

    def __init__(self):
        self.redis = RedisClient.get_instance()
        self.prefix = "session"

    def create_session(self, user_id: int, data: dict, ttl: int = 86400) -> str:
        """
        Create a new session

        Args:
            user_id: User ID
            data: Session data
            ttl: Time to live in seconds (default 24 hours)

        Returns:
            Session ID
        """
        import uuid

        session_id = str(uuid.uuid4())
        key = f"{self.prefix}:{session_id}"

        session_data = {"user_id": user_id, **data}

        self.redis.setex(key, ttl, json.dumps(session_data))
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        key = f"{self.prefix}:{session_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def update_session(self, session_id: str, data: dict, ttl: int = 86400):
        """Update session data"""
        key = f"{self.prefix}:{session_id}"
        current = self.get_session(session_id)
        if current:
            current.update(data)
            self.redis.setex(key, ttl, json.dumps(current))

    def delete_session(self, session_id: str):
        """Delete a session"""
        key = f"{self.prefix}:{session_id}"
        self.redis.delete(key)

    def get_user_sessions(self, user_id: int) -> list:
        """Get all sessions for a user"""
        pattern = f"{self.prefix}:*"
        sessions = []

        for key in self.redis.scan_iter(match=pattern):
            data = self.redis.get(key)
            if data:
                session_data = json.loads(data)
                if session_data.get("user_id") == user_id:
                    sessions.append({"session_id": key.split(":")[-1], **session_data})

        return sessions


class RateLimiter:
    """Rate limiting using Redis"""

    def __init__(self):
        self.redis = RedisClient.get_instance()
        self.prefix = "ratelimit"

    def is_allowed(
        self, identifier: str, max_requests: int = 100, window_seconds: int = 60
    ) -> bool:
        """
        Check if request is allowed under rate limit

        Args:
            identifier: Unique identifier (e.g., user_id, IP)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limit exceeded
        """
        key = f"{self.prefix}:{identifier}"
        current_count = self.redis.get(key)

        if current_count is None:
            # First request in window
            self.redis.setex(key, window_seconds, 1)
            return True

        if int(current_count) >= max_requests:
            return False

        # Increment counter
        self.redis.incr(key)
        return True

    def get_remaining(self, identifier: str, max_requests: int = 100) -> int:
        """Get remaining requests in current window"""
        key = f"{self.prefix}:{identifier}"
        current = self.redis.get(key)
        return max_requests - int(current or 0)


# Utility functions
def cache_query_result(key: str, data: dict, ttl: int = 300):
    """Cache database query result"""
    redis_client = RedisClient.get_instance()
    redis_client.setex(f"query:{key}", ttl, json.dumps(data))


def get_cached_query(key: str) -> Optional[dict]:
    """Get cached query result"""
    redis_client = RedisClient.get_instance()
    data = redis_client.get(f"query:{key}")
    return json.loads(data) if data else None


def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern"""
    redis_client = RedisClient.get_instance()
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
