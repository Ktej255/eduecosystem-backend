"""
Chatbot CRUD Operations
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.chatbot import ChatSession, ChatMessage, ChatFeedback
from app.schemas.chatbot import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatMessageCreate,
    ChatFeedbackCreate,
)
from datetime import datetime


# Chat Session CRUD
def create_chat_session(
    db: Session, session: ChatSessionCreate, user_id: int
) -> ChatSession:
    """Create a new chat session"""
    db_session = ChatSession(**session.model_dump(), user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_chat_session(db: Session, session_id: int) -> Optional[ChatSession]:
    """Get chat session by ID"""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_user_chat_sessions(
    db: Session,
    user_id: int,
    course_id: Optional[int] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> List[ChatSession]:
    """Get chat sessions for a user"""
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    if course_id:
        query = query.filter(ChatSession.course_id == course_id)

    if is_active is not None:
        query = query.filter(ChatSession.is_active == is_active)

    return query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()


def update_chat_session(
    db: Session, session_id: int, session_update: ChatSessionUpdate
) -> Optional[ChatSession]:
    """Update chat session"""
    db_session = get_chat_session(db, session_id)
    if not db_session:
        return None

    update_data = session_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)

    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_chat_session(db: Session, session_id: int) -> bool:
    """Delete chat session"""
    db_session = get_chat_session(db, session_id)
    if not db_session:
        return False

    db.delete(db_session)
    db.commit()
    return True


# Chat Message CRUD
def create_chat_message(db: Session, message: ChatMessageCreate) -> ChatMessage:
    """Create a new chat message"""
    db_message = ChatMessage(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Update session timestamp
    db_session = get_chat_session(db, message.session_id)
    if db_session:
        db_session.updated_at = datetime.utcnow()
        db.commit()

    return db_message


def get_session_messages(
    db: Session, session_id: int, limit: Optional[int] = None
) -> List[ChatMessage]:
    """Get all messages in a session"""
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    query = query.order_by(ChatMessage.created_at.asc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_recent_messages(
    db: Session, session_id: int, count: int = 10
) -> List[ChatMessage]:
    """Get recent messages for context"""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(count)
        .all()[::-1]
    )  # Reverse to chronological order


# Chat Feedback CRUD
def create_chat_feedback(
    db: Session, feedback: ChatFeedbackCreate, user_id: int
) -> ChatFeedback:
    """Create chat feedback"""
    db_feedback = ChatFeedback(**feedback.model_dump(), user_id=user_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_message_feedback(db: Session, message_id: int) -> Optional[ChatFeedback]:
    """Get feedback for a message"""
    return db.query(ChatFeedback).filter(ChatFeedback.message_id == message_id).first()
