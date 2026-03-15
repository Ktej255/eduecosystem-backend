from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any, List, Dict
from datetime import datetime, timedelta
from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.models.announcement import CourseAnnouncement
from app.models.discussion import DiscussionPost
from app.models.quiz import Quiz
from app.models.live_class import LiveClass
from app.models.lesson_progress import LessonProgress
from app.models.course_payment import CoursePayment

router = APIRouter()

@router.get("/leaderboard", response_model=List[Dict[str, Any]])
def get_teacher_leaderboard(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Composite Teacher Performance Scoring (0-100).
    Weights: 
    - Content Production (Courses/Quizzes): 30%
    - Engagement (Announcements/Discussions/Live): 40%
    - Student Success (Completion Rates/Avg Marks): 30%
    """
    # 1. Get all instructors
    teachers = db.query(User).filter(User.is_instructor == True).all()
    
    leaderboard = []
    
    for teacher in teachers:
        # --- A. Content Production (30 points max) ---
        course_count = db.query(func.count(Course.id)).filter(Course.instructor_id == teacher.id).scalar() or 0
        quiz_count = db.query(func.count(Quiz.id)).join(Course).filter(Course.instructor_id == teacher.id).scalar() or 0
        content_score = min(30, (course_count * 5) + (quiz_count * 1))

        # --- B. Engagement (40 points max) ---
        announcement_count = db.query(func.count(CourseAnnouncement.id)).filter(CourseAnnouncement.instructor_id == teacher.id).scalar() or 0
        live_count = db.query(func.count(LiveClass.id)).filter(LiveClass.instructor_id == teacher.id).scalar() or 0
        discussion_replies = db.query(func.count(DiscussionPost.id)).filter(DiscussionPost.user_id == teacher.id).scalar() or 0
        engagement_score = min(40, (announcement_count * 2) + (live_count * 5) + (discussion_replies * 0.5))

        # --- C. Student Success (30 points max) ---
        # Get all course IDs for this teacher
        teacher_courses = db.query(Course.id).filter(Course.instructor_id == teacher.id).all()
        tc_ids = [c.id for c in teacher_courses]
        
        success_score = 0
        if tc_ids:
            # Avg completion rate of their courses
            avg_completion = db.query(func.avg(LessonProgress.progress_percentage)).join(CoursePayment, CoursePayment.user_id == LessonProgress.user_id).filter(
                CoursePayment.course_id.in_(tc_ids)
            ).scalar() or 0
            success_score = min(30, (float(avg_completion) / 100) * 30)

        total_score = round(content_score + engagement_score + success_score, 2)
        
        leaderboard.append({
            "teacher_id": teacher.id,
            "name": teacher.full_name,
            "avatar": teacher.avatar_url,
            "total_score": total_score,
            "breakdown": {
                "content": content_score,
                "engagement": engagement_score,
                "success": success_score
            },
            "metrics": {
                "courses": course_count,
                "announcements": announcement_count,
                "live_sessions": live_count
            }
        })

    # Sort by total score descending
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    return leaderboard

@router.get("/{teacher_id}/deep-dive", response_model=Dict[str, Any])
def get_teacher_deep_dive(
    teacher_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Detailed performance analysis for a specific teacher."""
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        return {"error": "Teacher not found"}
        
    # Last 30 days activity trend
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    activity_count = db.query(func.count(CourseAnnouncement.id)).filter(
        CourseAnnouncement.instructor_id == teacher_id,
        CourseAnnouncement.created_at >= thirty_days_ago
    ).scalar() or 0
    
    return {
        "teacher_name": teacher.full_name,
        "recent_activity_count": activity_count,
        "is_top_performer": True if activity_count > 5 else False
    }
