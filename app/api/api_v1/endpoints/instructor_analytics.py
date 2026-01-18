"""
Unified Instructor Analytics & Monitoring Endpoints
Combines course performance with real-time student activity tracking.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.api import deps
from app.models.course import Course
from app.models.course_payment import CoursePayment
from app.models.user import User
from app.models.study_session import StudySession
from app.models.drill import DrillSession
from pydantic import BaseModel

router = APIRouter()

@router.get("/summary")
def get_instructor_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Unified analytics summary for instructors.
    Includes overview stats, enrollment trends, and live activity.
    """
    # 1. Instructor Context: Get all courses owned by this instructor
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]
    
    if not course_ids:
        return {
            "overview": {
                "total_students": 0,
                "total_revenue": 0,
                "avg_rating": 0,
                "total_courses": 0,
                "active_students": 0,
                "completion_rate": 0
            },
            "enrollment_trend": [],
            "revenue_by_course": [],
            "completion_stats": [],
            "top_courses": [],
            "live_activity": {"studying": 0, "drilling": 0}
        }

    # 2. Overview Calculations
    total_revenue = db.query(func.sum(CoursePayment.amount)).filter(
        CoursePayment.course_id.in_(course_ids),
        CoursePayment.status == "succeeded"
    ).scalar() or 0.0
    
    total_students = db.query(func.count(func.distinct(CoursePayment.user_id))).filter(
        CoursePayment.course_id.in_(course_ids),
        CoursePayment.status == "succeeded"
    ).scalar() or 0
    
    # Live Activity (Active sessions in the last 60 minutes for this instructor's topics/courses)
    # Note: In a real system, we'd filter sessions by the instructor's course topics.
    # For now, we show global activity as a proxy for platform health.
    hour_ago = datetime.utcnow() - timedelta(minutes=60)
    live_study_count = db.query(func.count(StudySession.id)).filter(
        StudySession.start_time >= hour_ago,
        StudySession.end_time.is_(None)
    ).scalar() or 0
    
    live_drill_count = db.query(func.count(DrillSession.id)).filter(
        DrillSession.created_at >= hour_ago,
        DrillSession.completed_at.is_(None)
    ).scalar() or 0

    # 3. Enrollment Trend (last N days)
    cutoff = datetime.utcnow() - timedelta(days=days)
    enrollments = db.query(
        func.date(CoursePayment.succeeded_at).label("date"),
        func.count(CoursePayment.id).label("count")
    ).filter(
        CoursePayment.course_id.in_(course_ids),
        CoursePayment.status == "succeeded",
        CoursePayment.succeeded_at >= cutoff
    ).group_by(func.date(CoursePayment.succeeded_at)).order_by("date").all()

    # 4. Top Performing Courses
    top_courses = []
    course_stats = db.query(
        CoursePayment.course_id,
        func.count(CoursePayment.id).label("students"),
        func.sum(CoursePayment.amount).label("revenue")
    ).filter(
        CoursePayment.course_id.in_(course_ids),
        CoursePayment.status == "succeeded"
    ).group_by(CoursePayment.course_id).order_by(desc("students")).limit(5).all()

    for stat in course_stats:
        course = next((c for c in courses if c.id == stat.course_id), None)
        if course:
            top_courses.append({
                "id": course.id,
                "title": course.title,
                "students": stat.students,
                "rating": 4.8, # Mocked rating for now
                "revenue": float(stat.revenue or 0)
            })

    return {
        "overview": {
            "total_students": total_students,
            "total_revenue": float(total_revenue),
            "avg_rating": 4.8,
            "total_courses": len(courses),
            "active_students": live_study_count + live_drill_count,
            "completion_rate": 85 # Mocked for now
        },
        "enrollment_trend": [{"date": str(e.date), "enrollments": e.count} for e in enrollments],
        "revenue_by_course": [{"course": c["title"][:15], "revenue": c["revenue"]} for c in top_courses],
        "completion_stats": [
            {"name": "Completed", "value": 65},
            {"name": "In Progress", "value": 25},
            {"name": "Not Started", "value": 10}
        ],
        "top_courses": top_courses,
        "live_activity": {
            "studying": live_study_count,
            "drilling": live_drill_count
        }
    }
