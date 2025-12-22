"""
Student Portal API Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.schemas.course import Course as CourseSchema
from pydantic import BaseModel

router = APIRouter()


class StudentCourseSummary(BaseModel):
    id: int
    title: str
    thumbnail: Optional[str] = None
    progress: int
    total_lessons: int
    completed_lessons: int
    next_lesson_id: Optional[int] = None
    next_lesson_title: Optional[str] = None


class StudentDashboardStats(BaseModel):
    active_courses: int
    avg_progress: int
    completed_courses: int
    total_learning_time: int  # in minutes
    streak_days: int


@router.get("/dashboard/stats", response_model=StudentDashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated stats for student dashboard
    """
    # Calculate active courses and progress
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    active_courses = len([e for e in enrollments if e.status == "active"])
    completed_courses = len([e for e in enrollments if e.status == "completed"])
    
    total_progress = sum([e.progress for e in enrollments]) if enrollments else 0
    avg_progress = int(total_progress / len(enrollments)) if enrollments else 0
    
    return {
        "active_courses": active_courses,
        "avg_progress": avg_progress,
        "completed_courses": completed_courses,
        "total_learning_time": 120,  # Mock data for now
        "streak_days": current_user.streak_days
    }


@router.get("/courses", response_model=List[StudentCourseSummary])
def get_student_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all courses for the student with progress
    """
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    
    courses_data = []
    for enrollment in enrollments:
        course = enrollment.course
        if not course:
            continue
            
        # Get total lessons
        total_lessons = 0
        for module in course.modules:
            total_lessons += len(module.lessons)
            
        # Get completed lessons
        completed_lessons = db.query(LessonProgress).filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.course_id == course.id,
            LessonProgress.is_completed == True
        ).count()
        
        # Find next lesson (first incomplete lesson)
        next_lesson_id = None
        next_lesson_title = None
        
        # Simple logic to find next lesson
        # In a real app, we'd query for the first lesson without a progress record or is_completed=False
        # For now, let's just return the first lesson of the first module if no progress
        if course.modules and course.modules[0].lessons:
            first_lesson = course.modules[0].lessons[0]
            next_lesson_id = first_lesson.id
            next_lesson_title = first_lesson.title
            
        courses_data.append({
            "id": course.id,
            "title": course.title,
            "thumbnail": course.thumbnail,
            "progress": enrollment.progress,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "next_lesson_id": next_lesson_id,
            "next_lesson_title": next_lesson_title
        })
        
    return courses_data


@router.get("/courses/{course_id}/funnel")
def get_course_funnel_data(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed course data for the funnel view
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
        
    # Build module/lesson structure with lock status
    modules_data = []
    for module in course.modules:
        lessons_data = []
        for lesson in module.lessons:
            # Check progress
            progress = db.query(LessonProgress).filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.lesson_id == lesson.id
            ).first()
            
            lessons_data.append({
                "id": lesson.id,
                "title": lesson.title,
                "duration": lesson.duration,
                "type": lesson.type,
                "is_completed": progress.is_completed if progress else False,
                "is_locked": False # Implement locking logic later
            })
            
        modules_data.append({
            "id": module.id,
            "title": module.title,
            "lessons": lessons_data
        })
        
    return {
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "thumbnail": course.thumbnail,
        },
        "progress": enrollment.progress,
        "modules": modules_data
    }
