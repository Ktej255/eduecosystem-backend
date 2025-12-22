from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app import models
from app.api import deps
from app.models.analytics import CourseAnalytics
from app.models.enrollment import Enrollment
from app.models.course_payment import CoursePayment
from app.models.course_review import CourseReview

router = APIRouter()


@router.get("/instructor/dashboard", response_model=dict)
def get_instructor_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get overview stats for instructor dashboard.
    """
    # Verify instructor status (assuming all users can be instructors for now, or check role)
    # if not user.is_instructor: ...

    # Get courses owned by user
    courses = (
        db.query(models.Course)
        .filter(models.Course.instructor_id == current_user.id)
        .all()
    )
    course_ids = [c.id for c in courses]

    if not course_ids:
        return {
            "total_revenue": 0,
            "total_students": 0,
            "active_courses": 0,
            "average_rating": 0,
            "monthly_revenue": 0,
            "monthly_enrollments": 0,
        }

    # Calculate totals
    total_students = (
        db.query(Enrollment).filter(Enrollment.course_id.in_(course_ids)).count()
    )
    active_courses = len(courses)

    # Revenue (sum of payments for these courses)
    total_revenue = (
        db.query(func.sum(CoursePayment.amount))
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "completed"
        )
        .scalar()
        or 0.0
    )

    # Average Rating
    avg_rating = (
        db.query(func.avg(CourseReview.rating))
        .filter(CourseReview.course_id.in_(course_ids))
        .scalar()
        or 0.0
    )

    # Monthly stats (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    monthly_revenue = (
        db.query(func.sum(CoursePayment.amount))
        .filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "completed",
            CoursePayment.created_at >= thirty_days_ago,
        )
        .scalar()
        or 0.0
    )

    monthly_enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id.in_(course_ids),
            Enrollment.enrolled_at >= thirty_days_ago,
        )
        .count()
    )

    return {
        "total_revenue": total_revenue,
        "total_students": total_students,
        "active_courses": active_courses,
        "average_rating": round(avg_rating, 1),
        "monthly_revenue": monthly_revenue,
        "monthly_enrollments": monthly_enrollments,
    }


@router.get("/instructor/courses/{course_id}/analytics", response_model=dict)
def get_course_analytics(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed analytics for a specific course.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Try to get cached analytics
    analytics = (
        db.query(CourseAnalytics).filter(CourseAnalytics.course_id == course_id).first()
    )

    # If not exists or old, calculate fresh (simplified for now, just calculate)
    # In production, we'd use a background task to update the cache

    total_enrollments = (
        db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
    )
    total_revenue = (
        db.query(func.sum(CoursePayment.amount))
        .filter(
            CoursePayment.course_id == course_id, CoursePayment.status == "completed"
        )
        .scalar()
        or 0.0
    )

    avg_rating = (
        db.query(func.avg(CourseReview.rating))
        .filter(CourseReview.course_id == course_id)
        .scalar()
        or 0.0
    )

    # Completion rate
    completed_count = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.status == "completed")
        .count()
    )
    completion_rate = (
        (completed_count / total_enrollments * 100) if total_enrollments > 0 else 0
    )

    return {
        "course_id": course_id,
        "title": course.title,
        "total_enrollments": total_enrollments,
        "total_revenue": total_revenue,
        "average_rating": round(avg_rating, 1),
        "completion_rate": round(completion_rate, 1),
    }


@router.get("/instructor/revenue-chart", response_model=List[dict])
def get_revenue_chart_data(
    days: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get daily revenue data for chart.
    """
    courses = (
        db.query(models.Course)
        .filter(models.Course.instructor_id == current_user.id)
        .all()
    )
    course_ids = [c.id for c in courses]

    if not course_ids:
        return []

    start_date = datetime.utcnow() - timedelta(days=days)

    # Group by date
    revenue_data = (
        db.query(
            func.date(CoursePayment.created_at).label("date"),
            func.sum(CoursePayment.amount).label("amount"),
        )
        .filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "completed",
            CoursePayment.created_at >= start_date,
        )
        .group_by(func.date(CoursePayment.created_at))
        .all()
    )

    # Format for frontend
    result = []
    # Fill in missing days would be better, but simple list for now
    for r in revenue_data:
        result.append({"date": str(r.date), "amount": r.amount})

    return result
