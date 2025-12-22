"""
Performance Monitoring and Benchmarking
Track API response times, database query performance, and system metrics
"""

import time
import logging
from functools import wraps
from typing import Callable, Dict, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics"""

    _metrics: Dict[str, List[float]] = defaultdict(list)
    _slow_queries: List[Dict] = []

    @classmethod
    def track_time(cls, operation: str):
        """Decorator to track operation execution time"""

        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    cls._record_metric(operation, duration)

                    # Log slow operations
                    if duration > 1.0:  # More than 1 second
                        logger.warning(
                            f"Slow operation: {operation} took {duration:.2f}s"
                        )
                        cls._slow_queries.append(
                            {
                                "operation": operation,
                                "duration": duration,
                                "timestamp": datetime.utcnow(),
                            }
                        )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    cls._record_metric(operation, duration)

                    if duration > 1.0:
                        logger.warning(
                            f"Slow operation: {operation} took {duration:.2f}s"
                        )
                        cls._slow_queries.append(
                            {
                                "operation": operation,
                                "duration": duration,
                                "timestamp": datetime.utcnow(),
                            }
                        )

            # Return appropriate wrapper based on function type
            import inspect

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    @classmethod
    def _record_metric(cls, operation: str, duration: float):
        """Record a metric"""
        cls._metrics[operation].append(duration)

        # Keep only last 1000 measurements per operation
        if len(cls._metrics[operation]) > 1000:
            cls._metrics[operation] = cls._metrics[operation][-1000:]

    @classmethod
    def get_stats(cls, operation: str = None) -> Dict:
        """Get performance statistics"""
        if operation:
            durations = cls._metrics.get(operation, [])
            if not durations:
                return {}

            return {
                "operation": operation,
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p50": sorted(durations)[len(durations) // 2],
                "p95": sorted(durations)[int(len(durations) * 0.95)],
                "p99": sorted(durations)[int(len(durations) * 0.99)],
            }

        # Return stats for all operations
        return {op: cls.get_stats(op) for op in cls._metrics.keys()}

    @classmethod
    def get_slow_queries(cls, limit: int = 10) -> List[Dict]:
        """Get recent slow queries"""
        return sorted(cls._slow_queries, key=lambda x: x["duration"], reverse=True)[
            :limit
        ]

    @classmethod
    def reset_metrics(cls):
        """Reset all metrics"""
        cls._metrics.clear()
        cls._slow_queries.clear()


# Middleware for request timing
async def performance_middleware(request, call_next):
    """Middleware to track request performance"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
        )

    return response


# Load testing configuration
LOAD_TEST_SCENARIOS = {
    "authentication": {
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/v1/auth/login",
                "body": {"username": "test@example.com", "password": "test"},
            },
        ],
        "users": 100,
        "duration": 60,
    },
    "course_browsing": {
        "endpoints": [
            {"method": "GET", "path": "/api/v1/courses/"},
            {"method": "GET", "path": "/api/v1/courses/1"},
            {"method": "GET", "path": "/api/v1/categories/"},
        ],
        "users": 500,
        "duration": 300,
    },
    "enrollment_flow": {
        "endpoints": [
            {"method": "GET", "path": "/api/v1/courses/1"},
            {"method": "POST", "path": "/api/v1/courses/1/enroll"},
            {"method": "GET", "path": "/api/v1/enrollments/my-courses"},
        ],
        "users": 200,
        "duration": 120,
    },
}


# Performance benchmarks (target metrics)
PERFORMANCE_TARGETS = {
    "api_response_time": {
        "p50": 0.1,  # 100ms
        "p95": 0.5,  # 500ms
        "p99": 1.0,  # 1 second
    },
    "database_query_time": {
        "p50": 0.05,  # 50ms
        "p95": 0.2,  # 200ms
        "p99": 0.5,  # 500ms
    },
    "page_load_time": {
        "p50": 2.0,  # 2 seconds
        "p95": 4.0,  # 4 seconds
        "p99": 6.0,  # 6 seconds
    },
}
