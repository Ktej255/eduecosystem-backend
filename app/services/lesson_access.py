from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.enrollment import Enrollment
from app.models.lesson_progress import LessonProgress
from app.crud.lesson_drip import lesson_drip
from app.schemas.lesson_drip import LessonAccessInfo


def check_lesson_access(
    db: Session, user_id: int, lesson_id: int, course_id: int
) -> LessonAccessInfo:
    """
    Check if a user has access to a specific lesson based on drip settings.

    Returns LessonAccessInfo with access status and unlock conditions.
    """
    # Check if user is enrolled in the course
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )

    if not enrollment:
        return LessonAccessInfo(has_access=False, reason="not_enrolled")

    # Check if lesson has drip settings
    drip_setting = lesson_drip.get_by_lesson(db, lesson_id)

    if not drip_setting or not drip_setting.is_active:
        # No active drip setting = full access
        return LessonAccessInfo(has_access=True, reason="no_drip")

    now = datetime.utcnow()

    # Date-based unlock
    if drip_setting.unlock_type == "date":
        if drip_setting.unlock_date and now >= drip_setting.unlock_date:
            return LessonAccessInfo(has_access=True, reason="date_unlocked")
        else:
            return LessonAccessInfo(
                has_access=False,
                reason="date_locked",
                unlock_date=drip_setting.unlock_date,
            )

    # Days after enrollment unlock
    elif drip_setting.unlock_type == "after_days":
        if not drip_setting.unlock_after_days:
            return LessonAccessInfo(has_access=True, reason="invalid_days_config")

        enrollment_date = enrollment.enrolled_at
        unlock_date = enrollment_date + timedelta(days=drip_setting.unlock_after_days)

        if now >= unlock_date:
            return LessonAccessInfo(has_access=True, reason="days_unlocked")
        else:
            days_remaining = (
                unlock_date - now
            ).days + 1  # Add 1 to include current day
            return LessonAccessInfo(
                has_access=False,
                reason="days_locked",
                unlock_date=unlock_date,
                days_remaining=days_remaining,
            )

    # Sequence-based unlock (prerequisite)
    elif drip_setting.unlock_type == "sequence":
        if not drip_setting.prerequisite_lesson_id:
            return LessonAccessInfo(has_access=True, reason="no_prerequisite")

        # Check if prerequisite lesson is completed
        prereq_progress = (
            db.query(LessonProgress)
            .filter(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == drip_setting.prerequisite_lesson_id,
                LessonProgress.is_completed == True,
            )
            .first()
        )

        if prereq_progress:
            return LessonAccessInfo(has_access=True, reason="prerequisite_completed")
        else:
            return LessonAccessInfo(
                has_access=False,
                reason="prerequisite_not_completed",
                prerequisite_lesson_id=drip_setting.prerequisite_lesson_id,
            )

    # Default: grant access
    return LessonAccessInfo(has_access=True, reason="default")
