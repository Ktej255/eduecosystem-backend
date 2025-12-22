"""
CRUD operations for AI Avatars
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.ai_avatar import AIAvatar
from app.schemas.ai_avatar import AIAvatarCreate, AIAvatarUpdate


class CRUDAIAvatar(CRUDBase[AIAvatar, AIAvatarCreate, AIAvatarUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[AIAvatar]:
        """Get all avatars for a specific user"""
        return (
            db.query(AIAvatar)
            .filter(AIAvatar.user_id == user_id)
            .order_by(AIAvatar.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_active_by_user(
        self, db: Session, *, user_id: int
    ) -> List[AIAvatar]:
        """Get all active avatars for a specific user"""
        return (
            db.query(AIAvatar)
            .filter(AIAvatar.user_id == user_id, AIAvatar.is_active == True)
            .order_by(AIAvatar.created_at.desc())
            .all()
        )
    
    def get_by_purpose(
        self, db: Session, *, user_id: int, purpose: str
    ) -> List[AIAvatar]:
        """Get avatars by purpose for a specific user"""
        return (
            db.query(AIAvatar)
            .filter(
                AIAvatar.user_id == user_id,
                AIAvatar.purpose == purpose,
                AIAvatar.is_active == True
            )
            .all()
        )


crud_ai_avatar = CRUDAIAvatar(AIAvatar)
