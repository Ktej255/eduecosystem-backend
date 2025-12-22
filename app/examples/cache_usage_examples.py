"""
Example of using Redis cache in API endpoints for improved performance.
This demonstrates how to cache expensive database queries and computations.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.core.redis_cache import get_cache
from app import models, schemas

router = APIRouter()


# Example 1: Cache a list of all courses
@router.get("/courses/cached", response_model=List[schemas.Course])
def get_courses_cached(
    skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)
):
    """
    Get all courses with caching enabled (5 minute TTL).
    This endpoint demonstrates basic caching of database queries.
    """
    cache = get_cache()
    cache_key = f"courses:list:{skip}:{limit}"

    # Try to get from cache
    if cache and cache.enabled:
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

    # Query database
    courses = db.query(models.Course).offset(skip).limit(limit).all()

    # Cache the result (5 minutes)
    if cache and cache.enabled:
        # Convert to dict for JSON serialization
        courses_data = [schemas.Course.from_orm(c).model_dump() for c in courses]
        cache.set(cache_key, courses_data, ttl=300)
        return courses_data

    return courses


# Example 2: Using the decorator for automatic caching
@router.get("/courses/{course_id}/stats")
def get_course_stats_cached(course_id: int, db: Session = Depends(deps.get_db)):
    """
    Get course statistics with caching (10 minute TTL).
    Uses decorator for cleaner code.
    """
    cache = get_cache()

    @cache.cache_response(ttl=600, key_prefix="course_stats")
    def fetch_stats():
        # Expensive computation/query
        enrollment_count = (
            db.query(models.Enrollment)
            .filter(models.Enrollment.course_id == course_id)
            .count()
        )

        avg_progress = (
            db.query(models.Enrollment)
            .filter(models.Enrollment.course_id == course_id)
            .with_entities(models.Enrollment.progress_percentage)
            .all()
        )

        return {
            "course_id": course_id,
            "total_enrollments": enrollment_count,
            "average_progress": sum([p[0] or 0 for p in avg_progress])
            / len(avg_progress)
            if avg_progress
            else 0,
        }

    return fetch_stats()


# Example 3: Cache invalidation when data changes
@router.post("/courses/{course_id}/enroll")
def enroll_in_course(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Enroll in a course and invalidate related caches.
    """
    # Create enrollment
    enrollment = models.Enrollment(user_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()

    # Invalidate caches
    cache = get_cache()
    if cache and cache.enabled:
        # Invalidate course stats cache
        cache.delete(f"course_stats:fetch_stats:*:{course_id}:*")

        # Invalidate user enrollments cache
        cache.delete(f"user:enrollments:{current_user.id}")

        # You could also invalidate all course-related caches
        # cache.invalidate_pattern("courses:*")

    return {"message": "Enrolled successfully", "enrollment_id": enrollment.id}


"""
Cache Strategy Guidelines:
==========================

1. **What to Cache:**
   - Frequently accessed, rarely changing data (e.g., course lists, categories)
   - Expensive computations (e.g., analytics, aggregations)
   - External API responses
   - User session data

2. **What NOT to Cache:**
   - User-specific sensitive data without proper isolation
   - Real-time data (e.g., live class participants)
   - Frequently updated data
   - Large objects (>1MB)

3. **TTL Guidelines:**
   - Static content: 1 hour - 24 hours
   - Dynamic content: 5-15 minutes
   - User session: 30 minutes - 1 hour
   - Analytics/Stats: 10-30 minutes

4. **Cache Invalidation:**
   - Invalidate on write operations (POST, PUT, DELETE)
   - Use pattern matching for bulk invalidation
   - Consider using cache tags for complex invalidation logic
   
5. **Performance Tips:**
   - Keep cache keys short but descriptive
   - Use compression for large values
   - Monitor cache hit/miss rates
   - Set appropriate TTLs based on data volatility
"""
