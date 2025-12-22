"""
CRUD operations for notifications
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate
from datetime import datetime


def get(db: Session, id: int) -> Optional[Notification]:
    """Get notification by ID"""
    return db.query(Notification).filter(Notification.id == id).first()


def get_multi_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
) -> List[Notification]:
    """Get notifications for a user"""
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    return (
        query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    )


def get_unread_count(db: Session, user_id: int) -> int:
    """Get count of unread notifications"""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )


def create(
    db: Session, obj_in: Union[NotificationCreate, Dict[str, Any]]
) -> Notification:
    """Create new notification"""
    obj_in_data = jsonable_encoder(obj_in)
    db_obj = Notification(**obj_in_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(
    db: Session, db_obj: Notification, obj_in: Union[NotificationUpdate, Dict[str, Any]]
) -> Notification:
    """Update notification"""
    obj_data = jsonable_encoder(db_obj)
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)

    for field in obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read for a user"""
    result = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True, "read_at": datetime.utcnow()})
    )
    db.commit()
    return result


def delete(db: Session, id: int) -> Notification:
    """Delete notification"""
    obj = db.query(Notification).get(id)
    db.delete(obj)
    db.commit()
    return obj
