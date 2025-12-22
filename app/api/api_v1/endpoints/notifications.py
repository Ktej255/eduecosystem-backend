from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.notification import Notification, NotificationList, UnreadCount
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("/", response_model=NotificationList)
def get_notifications(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get notifications for current user"""
    notifications = notification_service.get_user_notifications(
        db, current_user.id, skip, limit, unread_only
    )

    total = len(notifications)
    unread_count = notification_service.get_unread_count(db, current_user.id)

    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
    }


@router.get("/unread-count", response_model=UnreadCount)
def get_unread_count(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get unread notification count"""
    count = notification_service.get_unread_count(db, current_user.id)
    return {"count": count}


@router.post("/{notification_id}/read", response_model=Notification)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Mark a notification as read"""
    notification = notification_service.mark_as_read(
        db, notification_id, current_user.id
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    return notification


@router.post("/read-all")
def mark_all_as_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Mark all notifications as read"""
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Delete a notification"""
    success = notification_service.delete_notification(
        db, notification_id, current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    return {"message": "Notification deleted"}
