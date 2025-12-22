from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.crud import announcement as crud_announcement
from app.crud import permissions as crud_permissions
from app.schemas.announcement import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementListItem,
    AnnouncementInDBBase,
)

router = APIRouter()


@router.get(
    "/courses/{course_id}/announcements", response_model=List[AnnouncementListItem]
)
def list_announcements(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
) -> Any:
    """Get all announcements for a course"""
    # Check if user is enrolled or is instructor
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Get announcements
    announcements = crud_announcement.announcement.get_by_course(
        db, course_id=course_id, skip=skip, limit=limit
    )

    # Enhance with instructor info and read status
    result = []
    for ann in announcements:
        ann_dict = AnnouncementInDBBase.from_orm(ann).model_dump()
        ann_dict["instructor_name"] = (
            ann.instructor.full_name if ann.instructor else "Unknown"
        )
        ann_dict["is_read"] = crud_announcement.announcement.is_read_by_user(
            db, announcement_id=ann.id, user_id=current_user.id
        )
        result.append(ann_dict)

    return result


@router.get("/courses/{course_id}/announcements/unread-count")
def get_unread_count(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get count of unread announcements"""
    count = crud_announcement.announcement.get_unread_count(
        db, course_id=course_id, user_id=current_user.id
    )
    return {"unread_count": count}


@router.post(
    "/courses/{course_id}/announcements",
    response_model=Announcement,
    status_code=status.HTTP_201_CREATED,
)
def create_announcement(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    announcement_in: AnnouncementCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new announcement (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "create_announcement"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: create_announcement required",
            )

    # Verify course exists and user is instructor
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not the course instructor")

    announcement_in.course_id = course_id
    announcement = crud_announcement.announcement.create_with_instructor(
        db, obj_in=announcement_in, instructor_id=current_user.id
    )

    # Send announcement emails to all enrolled students
    try:
        from app.services.email_notification_service import send_announcement_email_sync
        from app.models.enrollment import Enrollment

        # Get all enrolled students
        enrollments = (
            db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
        )

        enrolled_students = []
        for enrollment in enrollments:
            student = db.query(User).filter(User.id == enrollment.student_id).first()
            if student:
                enrolled_students.append(student)

        if enrolled_students:
            send_announcement_email_sync(db, enrolled_students, announcement)
    except Exception as e:
        print(f"Failed to send announcement emails: {e}")

    # Enhance response
    ann_dict = Announcement.from_orm(announcement).model_dump()
    ann_dict["instructor_name"] = current_user.full_name
    ann_dict["instructor_avatar"] = getattr(current_user, "avatar_url", None)
    ann_dict["read_count"] = 0
    ann_dict["is_read"] = True

    return ann_dict


@router.get("/{announcement_id}", response_model=Announcement)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get announcement details"""
    announcement = crud_announcement.announcement.get(db, id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Enhance response
    ann_dict = Announcement.from_orm(announcement).model_dump()
    ann_dict["instructor_name"] = (
        announcement.instructor.full_name if announcement.instructor else "Unknown"
    )
    ann_dict["instructor_avatar"] = getattr(announcement.instructor, "avatar_url", None)
    ann_dict["read_count"] = len(announcement.reads)
    ann_dict["is_read"] = crud_announcement.announcement.is_read_by_user(
        db, announcement_id=announcement.id, user_id=current_user.id
    )

    return ann_dict


@router.put("/{announcement_id}", response_model=Announcement)
def update_announcement(
    announcement_id: int,
    *,
    db: Session = Depends(deps.get_db),
    announcement_in: AnnouncementUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update an announcement (instructor only)"""
    announcement = crud_announcement.announcement.get(db, id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Check permissions
    if announcement.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    announcement = crud_announcement.announcement.update(
        db, db_obj=announcement, obj_in=announcement_in
    )

    # Enhance response
    ann_dict = Announcement.from_orm(announcement).model_dump()
    ann_dict["instructor_name"] = (
        announcement.instructor.full_name if announcement.instructor else "Unknown"
    )
    ann_dict["read_count"] = len(announcement.reads)

    return ann_dict


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete an announcement (instructor only)"""
    announcement = crud_announcement.announcement.get(db, id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Check permissions
    if announcement.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud_announcement.announcement.remove(db, id=announcement_id)


@router.post("/{announcement_id}/mark-read")
def mark_announcement_as_read(
    announcement_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Mark announcement as read"""
    announcement = crud_announcement.announcement.get(db, id=announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    crud_announcement.announcement.mark_as_read(
        db, announcement_id=announcement_id, user_id=current_user.id
    )

    return {"message": "Marked as read"}
