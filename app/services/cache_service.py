"""
Database Query Optimization Service
Implements caching, query optimization, and performance monitoring
"""

import redis
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
    )
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None


class CacheService:
    """Redis caching service for query optimization"""

    @staticmethod
    def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """Generate unique cache key"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        if not redis_client:
            return None

        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (seconds)"""
        if not redis_client:
            return False

        try:
            redis_client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        if not redis_client:
            return False

        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not redis_client:
            return 0

        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")

        return 0


def cache_result(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results

    Usage:
        @cache_result('courses', ttl=600)
        def get_courses(db, skip=0, limit=20):
            return db.query(Course).offset(skip).limit(limit).all()
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = CacheService._generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached = CacheService.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {prefix}")
                return cached

            # Execute function
            logger.debug(f"Cache miss: {prefix}")
            result = func(*args, **kwargs)

            # Cache result
            CacheService.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class QueryOptimizer:
    """Database query optimization utilities"""

    @staticmethod
    def add_indexes(db):
        """Add recommended indexes for performance"""
        from sqlalchemy import text

        indexes = [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            # Course indexes
            "CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category_id);",
            "CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);",
            "CREATE INDEX IF NOT EXISTS idx_courses_published ON courses(is_published);",
            # Enrollment indexes
            "CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);",
            # Progress indexes
            "CREATE INDEX IF NOT EXISTS idx_progress_user ON lesson_progress(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_progress_lesson ON lesson_progress(lesson_id);",
            "CREATE INDEX IF NOT EXISTS idx_progress_completed ON lesson_progress(completed);",
            # Gamification indexes
            "CREATE INDEX IF NOT EXISTS idx_transactions_user ON coin_transactions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_created ON coin_transactions(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_achievements_user ON user_achievements(user_id);",
            # Discussion indexes
            "CREATE INDEX IF NOT EXISTS idx_threads_course ON discussion_threads(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_posts_thread ON discussion_posts(thread_id);",
            "CREATE INDEX IF NOT EXISTS idx_posts_created ON discussion_posts(created_at);",
        ]

        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
                logger.info("Index created/verified")
            except Exception as e:
                logger.warning(f"Index creation skipped: {e}")

        db.commit()

    @staticmethod
    def analyze_query_performance(db, query_str: str):
        """Analyze query performance using EXPLAIN"""
        from sqlalchemy import text

        try:
            result = db.execute(text(f"EXPLAIN QUERY PLAN {query_str}"))
            plan = result.fetchall()

            return {
                "query": query_str,
                "plan": [dict(row) for row in plan],
                "optimization_needed": any("SCAN" in str(row) for row in plan),
            }
        except Exception as e:
            logger.error(f"Query analysis error: {e}")
            return None


# Invalidation helpers
def invalidate_course_cache(course_id: int):
    """Invalidate all course-related caches"""
    CacheService.delete_pattern(f"*course*{course_id}*")
    CacheService.delete_pattern("courses*")


def invalidate_user_cache(user_id: int):
    """Invalidate all user-related caches"""
    CacheService.delete_pattern(f"*user*{user_id}*")
    CacheService.delete_pattern("users*")
