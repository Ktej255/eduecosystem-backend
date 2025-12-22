from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# Shared properties
class AIConversationBase(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None


class AIConversationCreate(AIConversationBase):
    initial_message: str


class AIConversationUpdate(AIConversationBase):
    messages: List[Dict[str, str]]


class AIConversationInDBBase(AIConversationBase):
    id: int
    user_id: int
    messages: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConversation(AIConversationInDBBase):
    pass


# API Request/Response Schemas


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    history: List[Dict[str, str]]


class ExplainRequest(BaseModel):
    concept: str
    level: str = "beginner"
    context: Optional[str] = None


class PracticeRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 3


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"


class StudyPlanRequest(BaseModel):
    goal: str
    duration: str
    hours_per_week: int
    current_knowledge: str
