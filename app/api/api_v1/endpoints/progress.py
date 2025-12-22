from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas
from app.api import deps
from app.models.lesson_progress import LessonProgress, ProgressStatus
from app.models.enrollment import Enrollment, EnrollmentStatus

router = APIRouter()


@router.post(
    "/lessons/{lesson_id}/mark-complete", response_model=schemas.LessonProgress
)
def mark_lesson_complete(
    lesson_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mark a lesson as complete.
    """
    # Check if lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check enrollment
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == lesson.module.course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    # Get or create progress
    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )

    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            status=ProgressStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            first_accessed_at=datetime.utcnow(),
        )
        db.add(progress)
    else:
        progress.status = ProgressStatus.COMPLETED
        progress.completed_at = datetime.utcnow()
        progress.last_accessed_at = datetime.utcnow()

    # Update enrollment last accessed lesson
    enrollment.last_accessed_lesson_id = lesson_id
    enrollment.last_accessed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)

    # Check course completion
    check_course_completion(db, current_user.id, lesson.module.course_id, enrollment)

    # Award coins for lesson completion
    try:
        from app.services.coin_service import trigger_coin_reward

        trigger_coin_reward(
            db=db,
            user=current_user,
            action="lesson_complete",
            reference_type="lesson",
            reference_id=lesson_id,
            description=f"Completed lesson: {lesson.title}",
        )
    except Exception as e:
        print(f"Failed to award coins for lesson completion: {e}")

    return progress


@router.post(
    "/lessons/{lesson_id}/update-progress", response_model=schemas.LessonProgress
)
def update_lesson_progress(
    lesson_id: int,
    progress_data: schemas.LessonProgressUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update lesson progress (e.g. video watch time).
    """
    # Check if lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check enrollment
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == lesson.module.course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    # Get or create progress
    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )

    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            status=ProgressStatus.IN_PROGRESS,
            first_accessed_at=datetime.utcnow(),
        )
        db.add(progress)

    # Update fields
    if progress_data.time_spent_seconds:
        progress.time_spent_seconds = progress_data.time_spent_seconds

    if progress_data.video_completed_percentage:
        progress.video_completed_percentage = progress_data.video_completed_percentage

        # Auto-complete if watched > 95%
        if (
            progress_data.video_completed_percentage >= 95.0
            and progress.status != ProgressStatus.COMPLETED
        ):
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = datetime.utcnow()
            # Check course completion
            check_course_completion(
                db, current_user.id, lesson.module.course_id, enrollment
            )

    progress.last_accessed_at = datetime.utcnow()
    enrollment.last_accessed_lesson_id = lesson_id
    enrollment.last_accessed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)
    return progress


@router.get("/courses/{course_id}/my-progress", response_model=schemas.CourseProgress)
def get_course_progress(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's progress for a course.
    """
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id, Enrollment.course_id == course_id
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Get all lessons in course
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    total_lessons = 0
    for module in course.modules:
        total_lessons += len(module.lessons)

    # Get completed lessons
    completed_lessons_count = (
        db.query(LessonProgress)
        .join(models.Lesson)
        .join(models.Module)
        .filter(
            LessonProgress.user_id == current_user.id,
            models.Module.course_id == course_id,
            LessonProgress.status == ProgressStatus.COMPLETED,
        )
        .count()
    )

    progress_percentage = 0.0
    if total_lessons > 0:
        progress_percentage = (completed_lessons_count / total_lessons) * 100

    # Update enrollment progress
    enrollment.progress_percentage = progress_percentage
    if progress_percentage >= 100.0 and enrollment.status != EnrollmentStatus.COMPLETED:
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.utcnow()

    db.commit()

    return {
        "course_id": course_id,
        "progress_percentage": progress_percentage,
        "completed_lessons": completed_lessons_count,
        "total_lessons": total_lessons,
        "status": enrollment.status,
        "completed_at": enrollment.completed_at,
    }


def check_course_completion(
    db: Session, user_id: int, course_id: int, enrollment: Enrollment
):
    """Helper to check and update course completion status"""
    # Count total lessons
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    total_lessons = 0
    for module in course.modules:
        total_lessons += len(module.lessons)

    # Count completed lessons
    completed_count = (
        db.query(LessonProgress)
        .join(models.Lesson)
        .join(models.Module)
        .filter(
            LessonProgress.user_id == user_id,
            models.Module.course_id == course_id,
            LessonProgress.status == ProgressStatus.COMPLETED,
        )
        .count()
    )

    # Calculate percentage
    percentage = 0.0
    if total_lessons > 0:
        percentage = (completed_count / total_lessons) * 100

    enrollment.progress_percentage = percentage

    # Mark completed if 100%
    if percentage >= 100.0 and enrollment.status != EnrollmentStatus.COMPLETED:
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = datetime.utcnow()

        # Generate certificate automatically
        from .certificates import generate_certificate_internal

        generate_certificate_internal(db, user_id, course_id, enrollment.id)

        # Award coins for course completion!
        try:
            from app.services.coin_service import trigger_coin_reward

            user = db.query(models.User).filter(models.User.id == user_id).first()

            if user:
                # Big reward for completing entire course
                trigger_coin_reward(
                    db=db,
                    user=user,
                    action="course_complete",
                    reference_type="course",
                    reference_id=course_id,
                    description=f"Completed course: {course.title}",
                )

                # Bonus for earning certificate
                trigger_coin_reward(
                    db=db,
                    user=user,
                    action="certificate_earn",
                    reference_type="course",
                    reference_id=course_id,
                    description=f"Certificate earned: {course.title}",
                )
        except Exception as e:
            print(f"Failed to award coins for course completion: {e}")

    db.commit()
