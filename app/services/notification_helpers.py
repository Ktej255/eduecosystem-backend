"""Helper functions for creating notifications and emitting via WebSocket"""

from sqlalchemy.orm import Session
from app.services.notification_service import notification_service
from app.models.notification import NotificationType
from app.websocket import manager
import asyncio


def create_and_emit_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    data: dict = None,
    action_url: str = None,
):
    """Create notification in DB and emit via WebSocket"""
    # Create notification
    notification = notification_service.create_notification(
        db=db,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        data=data or {},
        action_url=action_url,
    )

    # Emit via WebSocket (run async)
    try:
        asyncio.create_task(
            manager.send_notification_to_user(
                user_id=user_id,
                notification_data={
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "type": notification.type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "action_url": notification.action_url,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                },
            )
        )
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Error emitting notification: {e}")

    return notification
