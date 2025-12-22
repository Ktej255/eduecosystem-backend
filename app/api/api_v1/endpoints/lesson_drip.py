from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.course import Course
from app.schemas.lesson_drip import (
    DripSetting,
    DripSettingCreate,
    DripSettingUpdate,
    LessonAccessInfo,
)
from app.crud.lesson_drip import lesson_drip
from app.services.lesson_access import check_lesson_access

router = APIRouter()


@router.post(
    "/lessons/{lesson_id}/drip",
    response_model=DripSetting,
    status_code=status.HTTP_201_CREATED,
)
def create_drip_setting(
    lesson_id: int,
    *,
    db: Session = Depends(deps.get_db),
    drip_in: DripSettingCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create or update drip setting for a lesson (instructor only).
    """
    # Verify lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Get course to check instructor
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()

    # Check authorization
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this lesson"
        )

    # Check if drip setting already exists
    existing = lesson_drip.get_by_lesson(db, lesson_id)
    if existing:
        # Update existing
        return lesson_drip.update(
            db, existing.id, DripSettingUpdate(**drip_in.dict(exclude={"lesson_id"}))
        )

    # Set lesson_id
    drip_in.lesson_id = lesson_id

    # Create new drip setting
    return lesson_drip.create(db, drip_in)


@router.get("/lessons/{lesson_id}/drip", response_model=DripSetting)
def get_drip_setting(
    lesson_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get drip setting for a lesson.
    """
    drip_setting = lesson_drip.get_by_lesson(db, lesson_id)
    if not drip_setting:
        raise HTTPException(
            status_code=404, detail="No drip setting found for this lesson"
        )
    return drip_setting


@router.put("/drip/{drip_id}", response_model=DripSetting)
def update_drip_setting(
    drip_id: int,
    *,
    db: Session = Depends(deps.get_db),
    drip_in: DripSettingUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update drip setting (instructor only).
    """
    drip_setting = lesson_drip.get(db, drip_id)
    if not drip_setting:
        raise HTTPException(status_code=404, detail="Drip setting not found")

    # Get lesson and course to check authorization
    lesson = db.query(Lesson).filter(Lesson.id == drip_setting.lesson_id).first()
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    return lesson_drip.update(db, drip_id, drip_in)


@router.delete("/drip/{drip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drip_setting(
    drip_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete drip setting (instructor only).
    """
    drip_setting = lesson_drip.get(db, drip_id)
    if not drip_setting:
        raise HTTPException(status_code=404, detail="Drip setting not found")

    # Get lesson and course to check authorization
    lesson = db.query(Lesson).filter(Lesson.id == drip_setting.lesson_id).first()
    module = db.query(Module).filter(Module.id == lesson.module_id).first()
    course = db.query(Course).filter(Course.id == module.course_id).first()

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    lesson_drip.delete(db, drip_id)


@router.get("/lessons/{lesson_id}/access", response_model=LessonAccessInfo)
def check_access(
    lesson_id: int,
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check if current user has access to a lesson based on drip settings.
    """
    return check_lesson_access(db, current_user.id, lesson_id, course_id)
