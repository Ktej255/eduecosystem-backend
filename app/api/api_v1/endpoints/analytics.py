"""
Analytics API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.api import deps
from app.models.user import User
from app.schemas.analytics import (
    InstructorAnalyticsResponse,
    InstructorOverview,
    StudentAnalyticsResponse,
    PlatformAnalyticsResponse,
    EventCreate,
    EventResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_analytics(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Get comprehensive dashboard analytics for current user"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_dashboard_analytics(current_user.id)


@router.get("/detailed")
def get_detailed_analytics(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Get detailed analytics with advanced charts"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_detailed_analytics(current_user.id)

@router.get("/instructor/overview", response_model=InstructorOverview)
def get_instructor_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """Get instructor overview for last N days"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_instructor_overview(current_user.id, days)


@router.get(
    "/instructor/courses/{course_id}/performance",
    response_model=InstructorAnalyticsResponse,
)
def get_course_performance(
    course_id: int,
    target_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """Get detailed analytics for a specific course"""
    # Verify instructor owns the course
    from app.models.course import Course

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or course.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Course not found")

    analytics_service = AnalyticsService(db)
    analytics = analytics_service.calculate_instructor_analytics(
        current_user.id, course_id, target_date
    )

    return analytics


@router.get("/instructor/courses/{course_id}/students")
def get_course_students(
    course_id: int,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """Get list of students in course with their progress"""
    from app.models.course import Course
    from app.models.enrollment import Enrollment

    # Verify instructor owns the course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or course.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    analytics_service = AnalyticsService(db)
    students_data = []

    for enrollment in enrollments:
        student_analytics = analytics_service.calculate_student_analytics(
            enrollment.user_id, course_id
        )

        students_data.append(
            {
                "user_id": enrollment.user_id,
                "user_name": enrollment.user.full_name,
                "user_email": enrollment.user.email,
                "progress": enrollment.progress,
                "avg_quiz_score": student_analytics.avg_quiz_score,
                "last_active": enrollment.last_accessed,
                "at_risk": student_analytics.at_risk_flag,
                "engagement_score": student_analytics.engagement_score,
            }
        )

    return students_data


@router.get("/instructor/courses/{course_id}/revenue")
def get_course_revenue(
    course_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """Get revenue analytics for a course"""
    from app.models.course import Course
    from app.models.course_payment import CoursePayment

    # Verify instructor owns the course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or course.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Course not found")

    start_date = datetime.now() - timedelta(days=days)

    payments = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.course_id == course_id,
            CoursePayment.status == "completed",
            CoursePayment.created_at >= start_date,
        )
        .all()
    )

    total_revenue = sum(p.amount for p in payments)

    # Revenue by day
    revenue_trend = {}
    for payment in payments:
        day = payment.created_at.date()
        revenue_trend[day] = revenue_trend.get(day, 0) + payment.amount

    return {
        "total_revenue": total_revenue,
        "payments_count": len(payments),
        "avg_payment": total_revenue / len(payments) if payments else 0,
        "revenue_trend": [
            {"date": str(date), "revenue": amount}
            for date, amount in sorted(revenue_trend.items())
        ],
    }


@router.get("/instructor/courses/{course_id}/engagement")
def get_course_engagement(
    course_id: int,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """Get engagement metrics for a course"""
    from app.models.course import Course
    from app.models.discussion import DiscussionPost

    # Verify instructor owns the course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or course.instructor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Course not found")

    # Get all enrollments
    from app.models.enrollment import Enrollment

    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    # Calculate engagement metrics
    total_students = len(enrollments)
    active_students = len(
        [
            e
            for e in enrollments
            if e.last_accessed and (datetime.now() - e.last_accessed).days < 7
        ]
    )

    # Discussion participation
    posts = db.query(DiscussionPost).filter(DiscussionPost.course_id == course_id).all()

    return {
        "total_students": total_students,
        "active_students": active_students,
        "activity_rate": (active_students / total_students * 100)
        if total_students > 0
        else 0,
        "total_discussion_posts": len(posts),
        "avg_posts_per_student": len(posts) / total_students
        if total_students > 0
        else 0,
    }


# ===============================
# Student Analytics Endpoints
# ===============================


@router.get("/student/dashboard", response_model=StudentAnalyticsResponse)
def get_student_dashboard(
    course_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Get student's analytics dashboard for a course"""
    analytics_service = AnalyticsService(db)
    return analytics_service.calculate_student_analytics(current_user.id, course_id)


@router.get("/student/courses/{course_id}/insights")
def get_student_insights(
    course_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Get learning insights for student"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.calculate_student_analytics(
        current_user.id, course_id
    )

    # Determine learning style based on analytics
    learning_style = "balanced"
    if analytics.video_completion_rate > 0.8:
        learning_style = "visual"
    elif analytics.reading_completion_rate > 0.8:
        learning_style = "reading"
    elif analytics.quiz_preference > 0.7:
        learning_style = "interactive"

    return {
        "preferred_time_slot": analytics.preferred_time_slot or "evening",
        "learning_style": learning_style,
        "study_patterns": {
            "avg_session_duration": analytics.avg_session_duration,
            "total_sessions": analytics.sessions_count,
            "total_time_spent": analytics.total_time_spent,
        },
        "strengths": get_strengths(analytics),
        "areas_for_improvement": get_improvement_areas(analytics),
    }


@router.get("/student/progress-prediction")
def get_progress_prediction(
    course_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
):
    """Get progress predictions for student"""
    analytics_service = AnalyticsService(db)
    analytics = analytics_service.calculate_student_analytics(
        current_user.id, course_id
    )

    on_track = not analytics.at_risk_flag and analytics.engagement_score > 50

    recommendation = (
        "Keep up the great work!"
        if on_track
        else "Consider increasing your study time to stay on track."
    )

    return {
        "current_progress": analytics.completion_rate,
        "estimated_completion_date": analytics.estimated_completion_date,
        "estimated_days_remaining": analytics.estimated_days_to_complete,
        "on_track": on_track,
        "recommendation": recommendation,
    }


# ===============================
# Admin Analytics Endpoints
# ===============================


@router.get("/admin/platform-overview", response_model=PlatformAnalyticsResponse)
def get_platform_overview(
    target_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """Get platform-wide analytics overview"""
    analytics_service = AnalyticsService(db)
    return analytics_service.calculate_platform_analytics(target_date)


@router.get("/admin/trends")
def get_platform_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """Get platform trends over time"""
    from app.models.analytics import PlatformAnalytics

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    analytics_records = (
        db.query(PlatformAnalytics)
        .filter(
            PlatformAnalytics.date >= start_date, PlatformAnalytics.date <= end_date
        )
        .order_by(PlatformAnalytics.date)
        .all()
    )

    return {
        "user_trend": [
            {"date": str(a.date), "total": a.total_users, "active": a.active_users}
            for a in analytics_records
        ],
        "revenue_trend": [
            {"date": str(a.date), "revenue": a.total_revenue} for a in analytics_records
        ],
        "enrollment_trend": [
            {"date": str(a.date), "enrollments": a.enrollments_today}
            for a in analytics_records
        ],
    }


# ===============================
# Event Tracking
# ===============================


@router.post("/events", response_model=EventResponse)
def track_event(
    event: EventCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Track an analytics event"""
    analytics_service = AnalyticsService(db)
    return analytics_service.track_event(
        event_type=event.event_type,
        user_id=event.user_id or current_user.id,
        course_id=event.course_id,
        event_data=event.event_data,
        session_id=event.session_id,
    )


# ===============================
# Helper Functions
# ===============================


def get_strengths(analytics: StudentAnalyticsResponse) -> List[str]:
    """Identify student strengths based on analytics"""
    strengths = []

    if analytics.avg_quiz_score > 80:
        strengths.append("Strong quiz performance")
    if analytics.completion_rate > 70:
        strengths.append("Consistent progress")
    if analytics.discussion_posts > 10:
        strengths.append("Active in discussions")
    if analytics.avg_assignment_score > 85:
        strengths.append("Excellent assignment work")

    return strengths if strengths else ["Building foundation"]


def get_improvement_areas(analytics: StudentAnalyticsResponse) -> List[str]:
    """Identify areas for improvement"""
    areas = []

    if analytics.avg_quiz_score < 60:
        areas.append("Quiz preparation needs improvement")
    if analytics.completion_rate < 30:
        areas.append("Increase course engagement")
    if analytics.discussion_posts == 0:
        areas.append("Participate more in discussions")
    if analytics.at_risk_flag:
        areas.append("Stay active to avoid falling behind")

    return areas if areas else ["Keep up the good work!"]
