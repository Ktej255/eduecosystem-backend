"""
Chatbot API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.models.user import User
from app.schemas.chatbot import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    ChatSessionWithMessages,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatFeedbackCreate,
    ChatFeedback,
)
from app.crud import chatbot as crud_chatbot
from app.services.chatbot_service import chatbot_service
from app.core.redis_client import RateLimiter

router = APIRouter()
rate_limiter = RateLimiter()


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Send a message to the AI chatbot
    """
    # Rate limiting
    if not rate_limiter.is_allowed(
        f"chat:{current_user.id}", max_requests=20, window_seconds=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages.",
        )

    try:
        response = await chatbot_service.send_message(db, request, current_user)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )


@router.post("/sessions", response_model=ChatSession)
def create_session(
    session: ChatSessionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Create a new chat session"""
    return crud_chatbot.create_chat_session(db, session, current_user.id)


@router.get("/sessions", response_model=List[ChatSession])
def get_my_sessions(
    course_id: int = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get user's chat sessions"""
    return crud_chatbot.get_user_chat_sessions(
        db,
        current_user.id,
        course_id=course_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
def get_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get chat session with messages"""
    session = crud_chatbot.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

    return session


@router.put("/sessions/{session_id}", response_model=ChatSession)
def update_session(
    session_id: int,
    session_update: ChatSessionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Update chat session"""
    session = crud_chatbot.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud_chatbot.update_chat_session(db, session_id, session_update)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Delete chat session"""
    session = crud_chatbot.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud_chatbot.delete_chat_session(db, session_id)
    return {"message": "Session deleted successfully"}


@router.post("/feedback", response_model=ChatFeedback)
def submit_feedback(
    feedback: ChatFeedbackCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Submit feedback for a chatbot response"""
    return crud_chatbot.create_chat_feedback(db, feedback, current_user.id)
