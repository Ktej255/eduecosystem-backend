"""
Background tasks using Celery for async processing.

Tasks include:
- Email sending
- Report generation
- Analytics computation
- Notification processing
- Presence cleanup
"""

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.presence import presence_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="cleanup_stale_presence")
def cleanup_stale_presence():
    """
    Cleanup stale presence records (mark users as offline if inactive for 15+ minutes).
    Scheduled to run every 5 minutes.
    """
    db = SessionLocal()
    try:
        count = presence_service.cleanup_stale_presence(db, threshold_minutes=15)
        logger.info(f"Cleaned up {count} stale presence records")
        return {"status": "success", "cleaned_up": count}
    except Exception as e:
        logger.error(f"Error cleaning up stale presence: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_email")
def send_email_task(to_email: str, subject: str, body: str, html: bool = False):
    """
    Send email asynchronously.

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body
        html: Whether body is HTML
    """
    from app.services.email_notification_service import email_notification_service

    try:
        logger.info(f"Sending email to {to_email}: {subject}")

        # Use email notification service to send email
        db = SessionLocal()
        try:
            # Send the email
            success = email_notification_service.send_email(
                db=db, to_email=to_email, subject=subject, body=body, is_html=html
            )

            if success:
                logger.info(f"Email sent successfully to {to_email}")
                return {"status": "success", "to": to_email}
            else:
                logger.error(f"Failed to send email to {to_email}")
                return {
                    "status": "error",
                    "to": to_email,
                    "message": "Email sending failed",
                }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return {"status": "error", "to": to_email, "message": str(e)}


@celery_app.task(name="generate_report")
def generate_report_task(report_type: str, user_id: int, filters: dict):
    """
    Generate report asynchronously.

    Args:
        report_type: Type of report (student_progress, course_analytics, etc.)
        user_id: User requesting the report
        filters: Report filters and parameters
    """
    db = SessionLocal()
    try:
        logger.info(f"Generating {report_type} report for user {user_id}")

        # Implement basic report generation
        from app.models.enrollment import Enrollment

        report_data = {}

        if report_type == "student_progress":
            # Generate student progress report
            enrollments = (
                db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
            )
            report_data["total_courses"] = len(enrollments)
            report_data["completed_courses"] = len(
                [e for e in enrollments if e.completed]
            )

        elif report_type == "course_analytics":
            # Generate course analytics report
            course_id = filters.get("course_id")
            if course_id:
                enrollments = (
                    db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
                )
                report_data["total_enrollments"] = len(enrollments)
                report_data["completion_rate"] = (
                    len([e for e in enrollments if e.completed]) / len(enrollments)
                    if enrollments
                    else 0
                )

        logger.info(f"Report generated: {report_data}")

        return {
            "status": "success",
            "report_type": report_type,
            "user_id": user_id,
            "data": report_data,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute_analytics")
def compute_analytics_task(course_id: int = None):
    """
    Compute analytics metrics asynchronously.

    Args:
        course_id: Optional course ID to compute analytics for
    """
    db = SessionLocal()
    try:
        logger.info(f"Computing analytics for course {course_id or 'all courses'}")

        # Implement analytics computation
        from app.models.enrollment import Enrollment
        from sqlalchemy import func

        analytics = {}

        if course_id:
            # Compute analytics for specific course
            enrollments = (
                db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
            )

            total_enrollments = len(enrollments)
            completed_enrollments = len([e for e in enrollments if e.completed])

            analytics = {
                "course_id": course_id,
                "total_enrollments": total_enrollments,
                "completed_enrollments": completed_enrollments,
                "completion_rate": completed_enrollments / total_enrollments
                if total_enrollments > 0
                else 0,
                "active_students": len(
                    [e for e in enrollments if not e.completed and e.progress > 0]
                ),
            }
        else:
            # Compute platform-wide analytics
            total_enrollments = db.query(func.count(Enrollment.id)).scalar()
            analytics = {
                "total_platform_enrollments": total_enrollments,
                "computed_at": datetime.utcnow().isoformat(),
            }

        logger.info(f"Analytics computed: {analytics}")

        return {
            "status": "success",
            "course_id": course_id,
            "analytics": analytics,
            "computed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error computing analytics: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="process_notification")
def process_notification_task(notification_id: int):
    """
    Process and send notification asynchronously.

    Args:
        notification_id: Notification ID to process
    """
    db = SessionLocal()
    try:
        # Implement notification processing

        logger.info(f"Processing notification {notification_id}")

        # In a real implementation, this would:
        # 1. Fetch notification from database
        # 2. Determine notification type and recipients
        # 3. Send via appropriate channel (email, push, in-app)
        # 4. Update notification status

        # For now, we'll log and mark as processed
        logger.info(f"Notification {notification_id} processed successfully")

        return {
            "status": "success",
            "notification_id": notification_id,
            "processed_at": datetime.utcnow().isoformat(),
            "channels": ["in-app"],  # Could be extended to include email, push, etc.
        }
    except Exception as e:
        logger.error(f"Error processing notification: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


# Scheduled tasks configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks.
    """
    # Cleanup stale presence every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        cleanup_stale_presence.s(),
        name="cleanup-stale-presence-every-5min",
    )

    # Compute analytics every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour
        compute_analytics_task.s(),
        name="compute-analytics-every-hour",
    )
