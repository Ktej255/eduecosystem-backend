"""
Caching utilities using Redis
"""

import json
import functools
import logging
from typing import Any, Optional, Callable, Union
from datetime import timedelta
from app.core.redis_cache import get_cache

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis = None

    @property
    def client(self):
        if not self.redis:
            cache = get_cache()
            if cache and cache.enabled:
                self.redis = cache.redis_client
        return self.redis

    def is_available(self) -> bool:
        return self.client is not None

    async def get(self, key: str) -> Optional[Any]:
        if not self.is_available():
            return None
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: Union[int, timedelta] = 300) -> bool:
        if not self.is_available():
            return False
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_available():
            return 0
        try:
            count = 0
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.error(f"Cache delete pattern error {pattern}: {e}")
            return 0


cache = CacheService()


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache.is_available():
                return await func(*args, **kwargs)

            # Create cache key
            # Note: This is a simple key generation. For complex args,
            # might need more robust serialization
            arg_str = ":".join([str(a) for a in args])
            kwarg_str = ":".join([f"{k}={v}" for k, v in kwargs.items()])
            cache_key = f"{key_prefix}:{func.__name__}:{arg_str}:{kwarg_str}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache on function execution
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache.delete_pattern(pattern)
            return result

        return wrapper

    return decorator
