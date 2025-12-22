from typing import List
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from app.crud.base import CRUDBase
from app.models.ai_conversation import AIConversation
from app.schemas.ai_tutor import AIConversationCreate, AIConversationUpdate


class CRUDAIConversation(
    CRUDBase[AIConversation, AIConversationCreate, AIConversationUpdate]
):
    def create_with_user(
        self, db: Session, *, obj_in: AIConversationCreate, user_id: int
    ) -> AIConversation:
        obj_in_data = jsonable_encoder(obj_in)
        # Handle initial message separately if needed, or just init empty
        initial_message = obj_in_data.pop("initial_message", None)
        messages = []
        if initial_message:
            messages.append({"role": "user", "content": initial_message})

        db_obj = AIConversation(**obj_in_data, user_id=user_id, messages=messages)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AIConversation]:
        return (
            db.query(self.model)
            .filter(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_message(
        self, db: Session, *, conversation_id: int, role: str, content: str
    ) -> AIConversation:
        conversation = self.get(db, id=conversation_id)
        if not conversation:
            return None

        # Append new message to existing list
        # Note: We need to make a copy to ensure SQLAlchemy detects the change for JSON types in some DBs
        current_messages = list(conversation.messages) if conversation.messages else []
        current_messages.append({"role": role, "content": content})

        conversation.messages = current_messages
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation


ai_conversation = CRUDAIConversation(AIConversation)
