"""
CRUD operations for enrollments
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.models.enrollment import Enrollment, EnrollmentStatus


def get_enrollment(
    db: Session, *, course_id: int, student_id: int
) -> Optional[Enrollment]:
    """
    Get enrollment by course and student ID
    """
    return (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == student_id)
        .first()
    )


def create_enrollment(db: Session, *, user_id: int, course_id: int) -> Enrollment:
    """
    Create a new enrollment
    """
    enrollment = Enrollment(
        user_id=user_id, course_id=course_id, status=EnrollmentStatus.ACTIVE
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_enrollments_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Get all enrollments for a user
    """
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_enrollments_by_course(
    db: Session, course_id: int, skip: int = 0, limit: int = 100
):
    """
    Get all enrollments for a course
    """
    return (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_enrollment(db: Session, enrollment_id: int) -> bool:
    """
    Delete an enrollment
    """
    enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
    if enrollment:
        db.delete(enrollment)
        db.commit()
        return True
    return False
