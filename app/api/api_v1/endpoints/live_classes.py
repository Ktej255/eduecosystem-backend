from fastapi import APIRouter, Depends, HTTPException, Query
import os
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.api import deps
from app.crud import live_class as crud
from app.crud import permissions as crud_permissions
from app.crud import course as crud_course
from app.crud import enrollment as crud_enrollment
from app.schemas import live_class as schemas
from app.models.user import User
from app.models.live_class import LiveClassStatus

router = APIRouter()


@router.post("/courses/{course_id}/live-classes", response_model=schemas.LiveClass)
async def create_live_class(
    course_id: int,
    live_class: schemas.LiveClassCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new live class session.
    Instructor only.
    """
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "create_live_class"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: create_live_class required"
            )

        # Check if instructor of the course
        course = crud_course.course.get(db, id=course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the course instructor can create live classes",
            )
    if live_class.course_id != course_id:
        raise HTTPException(status_code=400, detail="Course ID mismatch")

    # Create video room
    try:
        from app.services.conference_service import conference_service

        room = await conference_service.create_room(
            name=f"class-{course_id}-{current_user.id}-{live_class.title.replace(' ', '-')[:20]}",
            privacy="public",  # For simplicity in MVP, can be private with tokens later
        )
        # Update meeting_url in schema before creating DB object
        # Note: We need to handle this carefully as schemas are immutable usually,
        # but here we are passing data to CRUD
        live_class.meeting_url = room.get("url")
        live_class.platform = "daily"
    except Exception as e:
        print(f"Failed to create video room: {e}")
        # Continue anyway, instructor can add link manually later

    return crud.create_live_class(db, live_class, current_user.id)


@router.get("/{live_class_id}/join-room", response_model=Dict[str, str])
def join_live_class_room(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get the video room URL for a live class.
    """
    live_class = crud.get_live_class(db, live_class_id)
    if not live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check access
    if not current_user.is_superuser:
        course = crud_course.course.get(db, id=live_class.course_id)
        if course:
            is_instructor = course.instructor_id == current_user.id
            is_enrolled = crud_enrollment.get_enrollment(
                db, course_id=live_class.course_id, student_id=current_user.id
            )

            if not (is_instructor or is_enrolled):
                raise HTTPException(
                    status_code=403, detail="Not enrolled in this course"
                )

    if not live_class.meeting_url:
        raise HTTPException(
            status_code=404, detail="No meeting URL available for this class"
        )

    return {"url": live_class.meeting_url}


@router.get("/{live_class_id}/agora-token", response_model=Dict[str, str])
def get_agora_token(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get Agora token for mobile app access
    """
    live_class = crud.get_live_class(db, live_class_id)
    if not live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check access (same logic as join-room)
    if not current_user.is_superuser:
        course = crud_course.course.get(db, id=live_class.course_id)
        if course:
            is_instructor = course.instructor_id == current_user.id
            is_enrolled = crud_enrollment.get_enrollment(
                db, course_id=live_class.course_id, student_id=current_user.id
            )

            if not (is_instructor or is_enrolled):
                raise HTTPException(
                    status_code=403, detail="Not enrolled in this course"
                )

    from app.services.conference_service import conference_service

    # Use live class ID or title as channel name
    channel_name = f"class-{live_class.course_id}-{live_class.id}"
    token = conference_service.generate_agora_token(channel_name, current_user.id)

    return {
        "token": token,
        "channel_name": channel_name,
        "app_id": os.getenv("AGORA_APP_ID", "mock-app-id"),
    }


@router.get("/webinars", response_model=List[schemas.LiveClass])
def get_all_webinars(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[LiveClassStatus] = None,
    upcoming_only: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Get all live classes/webinars across all courses.
    Admin only.
    """
    return crud.get_all_live_classes(
        db,
        skip=skip,
        limit=limit,
        status_filter=status,
        upcoming_only=upcoming_only,
    )


@router.get("/courses/{course_id}/live-classes", response_model=List[schemas.LiveClass])
def get_course_live_classes(
    course_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[LiveClassStatus] = None,
    upcoming_only: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all live classes for a course.
    Available to enrolled students and instructors.
    """
    # Check enrollment or instructor status
    if not current_user.is_superuser:
        course = crud_course.course.get(db, id=course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        is_instructor = course.instructor_id == current_user.id
        is_enrolled = crud_enrollment.get_enrollment(
            db, course_id=course_id, student_id=current_user.id
        )

        if not (is_instructor or is_enrolled):
            raise HTTPException(status_code=403, detail="Not enrolled in this course")
    return crud.get_live_classes_by_course(
        db,
        course_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        upcoming_only=upcoming_only,
    )


@router.get(
    "/courses/{course_id}/live-classes/upcoming", response_model=List[schemas.LiveClass]
)
def get_upcoming_live_classes(
    course_id: int,
    hours_ahead: int = Query(24, ge=1, le=168),  # Max 7 days
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get upcoming live classes within specified hours.
    """
    return crud.get_upcoming_live_classes(db, course_id, hours_ahead)


@router.get("/{live_class_id}", response_model=schemas.LiveClass)
def get_live_class(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get a specific live class by ID.
    """
    live_class = crud.get_live_class(db, live_class_id)
    if not live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check access
    if not current_user.is_superuser:
        course = crud_course.course.get(db, id=live_class.course_id)
        if course:
            is_instructor = course.instructor_id == current_user.id
            is_enrolled = crud_enrollment.get_enrollment(
                db, course_id=live_class.course_id, student_id=current_user.id
            )

            if not (is_instructor or is_enrolled):
                raise HTTPException(
                    status_code=403, detail="Not enrolled in this course"
                )
    return live_class


@router.put("/{live_class_id}", response_model=schemas.LiveClass)
def update_live_class(
    live_class_id: int,
    live_class_update: schemas.LiveClassUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a live class.
    Instructor only.
    """
    db_live_class = crud.get_live_class(db, live_class_id)
    if not db_live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check permission
    if not current_user.is_superuser:
        if db_live_class.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    updated = crud.update_live_class(db, live_class_id, live_class_update)
    return updated


@router.delete("/{live_class_id}")
def delete_live_class(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a live class.
    Instructor only.
    """
    db_live_class = crud.get_live_class(db, live_class_id)
    if not db_live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check permission
    if not current_user.is_superuser:
        if db_live_class.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    crud.delete_live_class(db, live_class_id)
    return {"message": "Live class deleted successfully"}


@router.post("/{live_class_id}/start", response_model=schemas.LiveClass)
def start_live_class(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Mark a live class as LIVE.
    Instructor only.
    """
    db_live_class = crud.get_live_class(db, live_class_id)
    if not db_live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    if db_live_class.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.start_live_class(db, live_class_id)


@router.post("/{live_class_id}/complete", response_model=schemas.LiveClass)
def complete_live_class(
    live_class_id: int,
    recording_url: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Mark a live class as COMPLETED and optionally add recording.
    Instructor only.
    """
    db_live_class = crud.get_live_class(db, live_class_id)
    if not db_live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    if db_live_class.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.complete_live_class(db, live_class_id, recording_url)


# Attendance endpoints
@router.post("/{live_class_id}/join", response_model=schemas.Attendance)
def join_live_class(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Record attendance when a student joins a live class.
    """
    live_class = crud.get_live_class(db, live_class_id)
    if not live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check enrollment
    if not current_user.is_superuser:
        is_enrolled = crud_enrollment.get_enrollment(
            db, course_id=live_class.course_id, student_id=current_user.id
        )
        if not is_enrolled:
            # Check if instructor
            course = crud_course.course.get(db, id=live_class.course_id)
            if not course or course.instructor_id != current_user.id:
                raise HTTPException(
                    status_code=403, detail="Not enrolled in this course"
                )

        # Check permission
        if not crud_permissions.check_permission(
            db, current_user.id, "join_live_class"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: join_live_class required"
            )

    return crud.record_attendance(db, live_class_id, current_user.id)


@router.get("/{live_class_id}/attendance", response_model=List[schemas.Attendance])
def get_live_class_attendance(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all attendance records for a live class.
    Instructor only.
    """
    live_class = crud.get_live_class(db, live_class_id)
    if not live_class:
        raise HTTPException(status_code=404, detail="Live class not found")

    # Check permission
    if not current_user.is_superuser:
        if live_class.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    return crud.get_attendance_by_live_class(db, live_class_id)


@router.get("/my-attendance", response_model=List[schemas.Attendance])
def get_my_attendance(
    course_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get attendance records for the current user.
    """
    return crud.get_student_attendance(db, current_user.id, course_id)
