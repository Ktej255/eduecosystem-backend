from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.notification import Notification, NotificationType
from datetime import datetime


class NotificationService:
    """Service for managing notifications"""

    def create_notification(
        self,
        db: Session,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = (
            query.order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return notifications

    def get_unread_count(self, db: Session, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        count = (
            db.query(Notification)
            .filter(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
            .count()
        )
        return count

    def mark_as_read(
        self, db: Session, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """Mark a notification as read"""
        notification = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
            )
            .first()
        )

        if notification:
            notification.mark_as_read()
            db.commit()
            db.refresh(notification)

        return notification

    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = (
            db.query(Notification)
            .filter(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )
        db.commit()
        return count

    def delete_notification(
        self, db: Session, notification_id: int, user_id: int
    ) -> bool:
        """Delete a notification"""
        notification = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
            )
            .first()
        )

        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

    def delete_old_notifications(self, db: Session, days: int = 30) -> int:
        """Delete notifications older than specified days"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        count = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff_date)
            .delete()
        )
        db.commit()
        return count


# Singleton instance
notification_service = NotificationService()
