from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.live_class import LiveClass, LiveClassAttendance, LiveClassStatus
from app.schemas import live_class as schemas


# LiveClass CRUD operations
def create_live_class(
    db: Session, live_class: schemas.LiveClassCreate, instructor_id: int
) -> LiveClass:
    """Create a new live class session"""
    db_live_class = LiveClass(**live_class.model_dump(), instructor_id=instructor_id)
    db.add(db_live_class)
    db.commit()
    db.refresh(db_live_class)
    return db_live_class


def get_live_class(db: Session, live_class_id: int) -> Optional[LiveClass]:
    """Get a live class by ID"""
    return db.query(LiveClass).filter(LiveClass.id == live_class_id).first()


def get_all_live_classes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LiveClassStatus] = None,
    upcoming_only: bool = False,
) -> List[LiveClass]:
    """Get all live classes with optional filters (admin use)"""
    query = db.query(LiveClass)

    if status_filter:
        query = query.filter(LiveClass.status == status_filter)

    if upcoming_only:
        query = query.filter(LiveClass.scheduled_at >= datetime.utcnow())

    return query.order_by(LiveClass.scheduled_at.desc()).offset(skip).limit(limit).all()


def get_live_classes_by_course(
    db: Session,
    course_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LiveClassStatus] = None,
    upcoming_only: bool = False,
) -> List[LiveClass]:
    """Get all live classes for a course with optional filters"""
    query = db.query(LiveClass).filter(LiveClass.course_id == course_id)

    if status_filter:
        query = query.filter(LiveClass.status == status_filter)

    if upcoming_only:
        query = query.filter(LiveClass.scheduled_at >= datetime.utcnow())

    return query.order_by(LiveClass.scheduled_at.desc()).offset(skip).limit(limit).all()


def get_upcoming_live_classes(
    db: Session, course_id: int, hours_ahead: int = 24
) -> List[LiveClass]:
    """Get upcoming live classes within specified hours"""
    now = datetime.utcnow()
    future = now + timedelta(hours=hours_ahead)

    return (
        db.query(LiveClass)
        .filter(
            and_(
                LiveClass.course_id == course_id,
                LiveClass.scheduled_at >= now,
                LiveClass.scheduled_at <= future,
                LiveClass.status == LiveClassStatus.SCHEDULED,
            )
        )
        .order_by(LiveClass.scheduled_at)
        .all()
    )


def update_live_class(
    db: Session, live_class_id: int, live_class_update: schemas.LiveClassUpdate
) -> Optional[LiveClass]:
    """Update a live class"""
    db_live_class = get_live_class(db, live_class_id)
    if not db_live_class:
        return None

    update_data = live_class_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_live_class, field, value)

    db.commit()
    db.refresh(db_live_class)
    return db_live_class


def delete_live_class(db: Session, live_class_id: int) -> bool:
    """Delete a live class"""
    db_live_class = get_live_class(db, live_class_id)
    if not db_live_class:
        return False

    db.delete(db_live_class)
    db.commit()
    return True


def start_live_class(db: Session, live_class_id: int) -> Optional[LiveClass]:
    """Mark a live class as LIVE"""
    db_live_class = get_live_class(db, live_class_id)
    if not db_live_class:
        return None

    db_live_class.status = LiveClassStatus.LIVE
    db.commit()
    db.refresh(db_live_class)
    return db_live_class


def complete_live_class(
    db: Session, live_class_id: int, recording_url: Optional[str] = None
) -> Optional[LiveClass]:
    """Mark a live class as COMPLETED and optionally add recording"""
    db_live_class = get_live_class(db, live_class_id)
    if not db_live_class:
        return None

    db_live_class.status = LiveClassStatus.COMPLETED
    if recording_url:
        db_live_class.recording_url = recording_url
        db_live_class.recording_available = True

    db.commit()
    db.refresh(db_live_class)
    return db_live_class


# Attendance CRUD operations
def record_attendance(
    db: Session, live_class_id: int, student_id: int
) -> LiveClassAttendance:
    """Record that a student joined a live class"""
    # Check if already attended
    existing = (
        db.query(LiveClassAttendance)
        .filter(
            and_(
                LiveClassAttendance.live_class_id == live_class_id,
                LiveClassAttendance.student_id == student_id,
            )
        )
        .first()
    )

    if existing:
        return existing

    attendance = LiveClassAttendance(
        live_class_id=live_class_id, student_id=student_id, joined_at=datetime.utcnow()
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def update_attendance(
    db: Session, attendance_id: int, attendance_update: schemas.AttendanceUpdate
) -> Optional[LiveClassAttendance]:
    """Update attendance record (e.g., when student leaves)"""
    attendance = (
        db.query(LiveClassAttendance)
        .filter(LiveClassAttendance.id == attendance_id)
        .first()
    )
    if not attendance:
        return None

    update_data = attendance_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)
    return attendance


def get_attendance_by_live_class(
    db: Session, live_class_id: int
) -> List[LiveClassAttendance]:
    """Get all attendance records for a live class"""
    return (
        db.query(LiveClassAttendance)
        .filter(LiveClassAttendance.live_class_id == live_class_id)
        .all()
    )


def get_student_attendance(
    db: Session, student_id: int, course_id: Optional[int] = None
) -> List[LiveClassAttendance]:
    """Get all attendance records for a student, optionally filtered by course"""
    query = db.query(LiveClassAttendance).filter(
        LiveClassAttendance.student_id == student_id
    )

    if course_id:
        query = query.join(LiveClass).filter(LiveClass.course_id == course_id)

    return query.all()
