"""
Chatbot Pydantic Schemas
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# Chat Session Schemas
class ChatSessionBase(BaseModel):
    title: Optional[str] = "New Chat"
    course_id: Optional[int] = None
    context_type: str = "general"
    context_id: Optional[int] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessages(ChatSession):
    messages: List["ChatMessage"] = []


# Chat Message Schemas
class ChatMessageBase(BaseModel):
    content: str
    role: str = "user"


class ChatMessageCreate(ChatMessageBase):
    session_id: int
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    metadata: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Chat Request/Response
class ChatRequest(BaseModel):
    """Request to send a message to chatbot"""

    message: str
    session_id: Optional[int] = None
    course_id: Optional[int] = None
    context_type: Optional[str] = "general"
    context_id: Optional[int] = None


class ChatResponse(BaseModel):
    """Chatbot response"""

    session_id: int
    message: ChatMessage
    response: ChatMessage
    suggestions: Optional[List[str]] = None


# Chat Feedback Schemas
class ChatFeedbackCreate(BaseModel):
    message_id: int
    rating: Optional[int] = None
    is_helpful: Optional[bool] = None
    feedback_text: Optional[str] = None


class ChatFeedback(ChatFeedbackCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
