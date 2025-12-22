from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.live_class_interactive import PollStatus


# Poll Schemas
class PollOption(BaseModel):
    text: str
    index: int


class PollCreate(BaseModel):
    question: str
    options: List[str]
    correct_option_index: Optional[int] = None


class PollResponseCreate(BaseModel):
    poll_id: int
    selected_option_index: int


class PollResponse(BaseModel):
    id: int
    poll_id: int
    question: str
    options: List[str]
    status: PollStatus
    created_at: datetime
    responses_count: int = 0
    user_response_index: Optional[int] = None  # If current user responded

    model_config = ConfigDict(from_attributes=True)


# Question Schemas
class QuestionCreate(BaseModel):
    question_text: str


class QuestionAnswer(BaseModel):
    answer_text: str


class QuestionResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    question_text: str
    is_answered: bool
    answer_text: Optional[str]
    upvotes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Chat Schemas
class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    message: str
    is_instructor: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Reaction Schema
class ReactionCreate(BaseModel):
    reaction_type: str
