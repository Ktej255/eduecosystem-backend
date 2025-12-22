"""
Redis caching layer for API responses and frequently accessed data.
Provides decorators and utilities for caching to improve performance.
"""

from typing import Optional, Callable, Any
from functools import wraps
import json
import hashlib
import logging
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """Central cache manager for Redis operations"""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection"""
        self.redis_client: Optional[Redis] = None
        self.enabled = False

        if redis_url:
            try:
                self.redis_client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("Redis cache initialized successfully")
            except RedisError as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.redis_client = None
                self.enabled = False

    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function name and arguments"""
        # Create a stable string representation
        key_parts = [func_name]

        # Add args (skip 'self' or 'cls')
        for arg in args:
            if hasattr(arg, "__dict__"):
                continue  # Skip class instances
            key_parts.append(str(arg))

        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")

        # Hash to keep key length manageable
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"cache:{func_name}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (time to live in seconds)"""
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except RedisError as e:
            logger.warning(f"Cache invalidate error: {e}")
        return 0

    def cache_response(self, ttl: int = 300, key_prefix: str = ""):
        """
        Decorator to cache function responses

        Args:
            ttl: Time to live in seconds (default 5 minutes)
            key_prefix: Optional prefix for cache key
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                # Generate cache key
                func_name = (
                    f"{key_prefix}{func.__name__}" if key_prefix else func.__name__
                )
                cache_key = self._generate_key(func_name, *args, **kwargs)

                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached

                # Execute function and cache result
                logger.debug(f"Cache miss: {cache_key}")
                result = await func(*args, **kwargs)

                # Cache the result
                self.set(cache_key, result, ttl)
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # Generate cache key
                func_name = (
                    f"{key_prefix}{func.__name__}" if key_prefix else func.__name__
                )
                cache_key = self._generate_key(func_name, *args, **kwargs)

                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached

                # Execute function and cache result
                logger.debug(f"Cache miss: {cache_key}")
                result = func(*args, **kwargs)

                # Cache the result
                self.set(cache_key, result, ttl)
                return result

            # Return appropriate wrapper based on function type
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator


# Global cache instance (initialized in main.py)
cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get the global cache manager instance"""
    return cache_manager


def init_cache(redis_url: Optional[str] = None) -> CacheManager:
    """Initialize the global cache manager"""
    global cache_manager
    cache_manager = CacheManager(redis_url)
    return cache_manager
