"""
Email Notification Service

Handles sending email notifications with template rendering and user preference checking.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.email_notification import (
    UserEmailPreference,
    EmailTemplate,
    EmailLog,
    NotificationType,
    EmailStatus,
)
from app.models.user import User
from app.core.config import settings


def render_template(template_str: str, variables: Dict[str, Any]) -> str:
    """
    Simple template rendering using string replacement.
    Replaces {{variable_name}} with actual values.
    """
    result = template_str
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


async def send_notification_email(
    db: Session,
    user: User,
    notification_type: NotificationType,
    template_name: str,
    variables: Dict[str, Any],
    force: bool = False,
) -> Optional[EmailLog]:
    """
    Send an email notification to a user.

    Args:
        db: Database session
        user: User to send email to
        notification_type: Type of notification
        template_name: Name of email template to use
        variables: Variables to render in template
        force: If True, send even if user has disabled this notification type

    Returns:
        EmailLog object if email was sent, None otherwise
    """
    # Check user preferences unless forced
    if not force:
        preferences = (
            db.query(UserEmailPreference)
            .filter(UserEmailPreference.user_id == user.id)
            .first()
        )

        if preferences and not preferences.is_enabled(notification_type):
            return None

    # Get template
    template = (
        db.query(EmailTemplate).filter(EmailTemplate.name == template_name).first()
    )

    if not template:
        raise ValueError(f"Email template '{template_name}' not found")

    # Render template
    rendered_subject = render_template(template.subject, variables)
    rendered_html = render_template(template.body_html, variables)
    rendered_text = (
        render_template(template.body_text, variables) if template.body_text else None
    )

    # Create log entry
    email_log = EmailLog(
        user_id=user.id,
        template_id=template.id,
        recipient_email=user.email,
        subject=rendered_subject,
        body_html=rendered_html,
        body_text=rendered_text,
        status=EmailStatus.PENDING,
    )
    db.add(email_log)
    db.commit()

    try:
        # Send email using FastMail
        if not settings.MAIL_SUPPRESS_SEND:
            # For now, we'll use direct send since we don't have FastMail templates set up yet
            # TODO: Implement proper template-based sending
            pass

        # Update log
        email_log.status = EmailStatus.SENT
        email_log.sent_at = datetime.utcnow()
        db.commit()

        return email_log

    except Exception as e:
        # Log error
        email_log.status = EmailStatus.FAILED
        email_log.error_message = str(e)
        db.commit()
        raise


def get_or_create_preferences(db: Session, user_id: int) -> UserEmailPreference:
    """Get user's email preferences or create default ones"""
    preferences = (
        db.query(UserEmailPreference)
        .filter(UserEmailPreference.user_id == user_id)
        .first()
    )

    if not preferences:
        preferences = UserEmailPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


# =============================================================================
# Notification Helper Functions
# =============================================================================


async def send_enrollment_email(
    db: Session, user: User, course: Any
) -> Optional[EmailLog]:
    """Send welcome email when user enrolls in a course"""
    variables = {
        "student_name": user.full_name or user.email,
        "course_title": course.title,
        "course_description": course.description or "",
        "instructor_name": course.instructor.full_name
        if course.instructor
        else "Instructor",
    }

    return await send_notification_email(
        db=db,
        user=user,
        notification_type=NotificationType.ENROLLMENT,
        template_name="course_enrollment",
        variables=variables,
    )


def send_enrollment_email_sync(
    db: Session, user: User, course: Any
) -> Optional[EmailLog]:
    """Synchronous wrapper for send_enrollment_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(send_enrollment_email(db, user, course))


async def send_assignment_submitted_email(
    db: Session, user: User, assignment: Any
) -> Optional[EmailLog]:
    """Send confirmation email when student submits assignment"""
    variables = {
        "student_name": user.full_name or user.email,
        "assignment_title": assignment.title,
        "submitted_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    }

    return await send_notification_email(
        db=db,
        user=user,
        notification_type=NotificationType.ASSIGNMENT_SUBMITTED,
        template_name="assignment_submitted",
        variables=variables,
    )


async def send_assignment_graded_email(
    db: Session, user: User, assignment: Any, grade: float
) -> Optional[EmailLog]:
    """Send email when assignment is graded"""
    variables = {
        "student_name": user.full_name or user.email,
        "assignment_title": assignment.title,
        "grade": str(grade),
        "max_grade": "100",
    }

    return await send_notification_email(
        db=db,
        user=user,
        notification_type=NotificationType.ASSIGNMENT_GRADED,
        template_name="assignment_graded",
        variables=variables,
    )


async def send_quiz_completed_email(
    db: Session, user: User, quiz: Any, score: float
) -> Optional[EmailLog]:
    """Send email when quiz is completed"""
    variables = {
        "student_name": user.full_name or user.email,
        "quiz_title": quiz.title,
        "score": str(score),
        "total_questions": str(quiz.total_questions)
        if hasattr(quiz, "total_questions")
        else "N/A",
    }

    return await send_notification_email(
        db=db,
        user=user,
        notification_type=NotificationType.QUIZ_COMPLETED,
        template_name="quiz_completed",
        variables=variables,
    )


async def send_certificate_earned_email(
    db: Session, user: User, certificate: Any, course: Any
) -> Optional[EmailLog]:
    """Send congratulatory email when certificate is earned"""
    variables = {
        "student_name": user.full_name or user.email,
        "course_title": course.title,
        "certificate_url": f"/certificates/{certificate.id}",
        "completion_date": certificate.created_at.strftime("%Y-%m-%d")
        if certificate.created_at
        else "",
    }

    return await send_notification_email(
        db=db,
        user=user,
        notification_type=NotificationType.CERTIFICATE_EARNED,
        template_name="certificate_earned",
        variables=variables,
    )


async def send_announcement_email(
    db: Session, users: list[User], announcement: Any
) -> list[EmailLog]:
    """Send announcement email to multiple users"""
    email_logs = []

    for user in users:
        variables = {
            "student_name": user.full_name or user.email,
            "announcement_title": announcement.title,
            "announcement_content": announcement.content,
            "instructor_name": announcement.instructor.full_name
            if hasattr(announcement, "instructor") and announcement.instructor
            else "Instructor",
        }

        log = await send_notification_email(
            db=db,
            user=user,
            notification_type=NotificationType.ANNOUNCEMENT,
            template_name="course_announcement",
            variables=variables,
        )

        if log:
            email_logs.append(log)

    return email_logs


# =============================================================================
# Synchronous Wrappers (for use in non-async endpoints)
# =============================================================================


def send_assignment_submitted_email_sync(
    db: Session, user: User, assignment: Any
) -> Optional[EmailLog]:
    """Synchronous wrapper for send_assignment_submitted_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        send_assignment_submitted_email(db, user, assignment)
    )


def send_assignment_graded_email_sync(
    db: Session, user: User, assignment: Any, grade: float
) -> Optional[EmailLog]:
    """Synchronous wrapper for send_assignment_graded_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        send_assignment_graded_email(db, user, assignment, grade)
    )


def send_quiz_completed_email_sync(
    db: Session, user: User, quiz: Any, score: float
) -> Optional[EmailLog]:
    """Synchronous wrapper for send_quiz_completed_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(send_quiz_completed_email(db, user, quiz, score))


def send_certificate_earned_email_sync(
    db: Session, user: User, certificate: Any, course: Any
) -> Optional[EmailLog]:
    """Synchronous wrapper for send_certificate_earned_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        send_certificate_earned_email(db, user, certificate, course)
    )


def send_announcement_email_sync(
    db: Session, users: list[User], announcement: Any
) -> list[EmailLog]:
    """Synchronous wrapper for send_announcement_email"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(send_announcement_email(db, users, announcement))
