from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas
from app.api import deps
from app.models.enrollment import EnrollmentStatus

router = APIRouter()


@router.get("/courses/{course_id}/certificate", response_model=schemas.Certificate)
def get_course_certificate(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get certificate for a course. Generates one if eligible but missing.
    """
    # Check enrollment
    enrollment = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.course_id == course_id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Check existing certificate
    certificate = (
        db.query(models.Certificate)
        .filter(models.Certificate.enrollment_id == enrollment.id)
        .first()
    )

    if certificate:
        return certificate

    # Check eligibility
    if (
        enrollment.status != EnrollmentStatus.COMPLETED
        and enrollment.progress_percentage < 100.0
    ):
        raise HTTPException(status_code=400, detail="Course not completed yet")

    # Generate new certificate
    return generate_certificate_internal(db, current_user.id, course_id, enrollment.id)


@router.get("/my-certificates", response_model=List[schemas.Certificate])
def get_my_certificates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all certificates for current user.
    """
    certificates = (
        db.query(models.Certificate)
        .filter(models.Certificate.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return certificates


@router.get("/{certificate_number}/download")
def download_certificate(
    certificate_number: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Download certificate PDF.
    """
    certificate = (
        db.query(models.Certificate)
        .filter(models.Certificate.certificate_number == certificate_number)
        .first()
    )

    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Verify ownership (or allow public verification later)
    if certificate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # In a real app, this would return a signed S3 URL or generate PDF on fly
    # For now, return mock data
    return {
        "download_url": f"/static/certificates/{certificate.certificate_number}.pdf",
        "html_preview": f"<h1>Certificate for {certificate.student_name}</h1>",
    }


def generate_certificate_internal(
    db: Session, user_id: int, course_id: int, enrollment_id: int
):
    """Internal helper to generate certificate and mine block"""
    from app.services.blockchain_service import blockchain_service
    from app.services.notification_helpers import create_and_emit_notification
    from app.models.notification import NotificationType
    import uuid

    user = db.query(models.User).get(user_id)
    course = db.query(models.Course).get(course_id)

    # Create certificate record
    cert_number = f"CERT-{uuid.uuid4().hex[:8].upper()}"
    certificate = models.Certificate(
        user_id=user_id,
        course_id=course_id,
        enrollment_id=enrollment_id,
        certificate_number=cert_number,
        issued_at=datetime.utcnow(),
        student_name=user.full_name,
        student_email=user.email,
        course_title=course.title,
        instructor_name=course.instructor.full_name
        if course.instructor
        else "Instructor",
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    # Mine block for immutable record
    block_data = {
        "certificate_id": certificate.id,
        "certificate_number": cert_number,
        "student_name": user.full_name,
        "course_title": course.title,
        "issued_at": str(certificate.issued_at),
        "issuer": "Eduecosystem Platform",
    }

    service = blockchain_service(db)
    block = service.add_block(block_data)

    # Link certificate to block
    certificate.blockchain_hash = block.hash
    db.commit()

    # Notify user
    create_and_emit_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.CERTIFICATE_ISSUED,
        title="Certificate Issued",
        message=f"Congratulations! You've earned a certificate for {course.title}.",
        data={"certificate_id": certificate.id, "hash": block.hash},
        action_url="/lms/my-certificates",
    )

    # Send certificate earned email
    try:
        from app.services.email_notification_service import (
            send_certificate_earned_email_sync,
        )

        send_certificate_earned_email_sync(db, user, certificate, course)
    except Exception as e:
        print(f"Failed to send certificate email: {e}")

    return certificate
