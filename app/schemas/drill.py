"""
Pydantic schemas for Drill System
Request/Response models for API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# Question Schemas
class QuestionSection(BaseModel):
    heading: str
    text: str


class QuestionCreate(BaseModel):
    gs_paper: str = Field(..., pattern="^GS[1-4]$")
    topic: str
    sub_topic: Optional[str] = None
    question_text: str
    key_points: List[str]
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuestionUpdate(BaseModel):
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    question_text: Optional[str] = None
    key_points: Optional[List[str]] = None
    difficulty: Optional[str] = None


class QuestionResponse(BaseModel):
    id: UUID
    gs_paper: str
    topic: str
    sub_topic: Optional[str]
    question_text: str
    key_points: List[str]
    difficulty: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Content Schemas
class ContentCreate(BaseModel):
    question_id: UUID
    title: str
    sections: List[Dict[str, str]]  # [{heading, text}]
    estimated_reading_time: int = 60


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    sections: Optional[List[Dict[str, str]]] = None
    estimated_reading_time: Optional[int] = None


class ContentResponse(BaseModel):
    id: UUID
    question_id: UUID
    title: str
    sections: List[Dict[str, str]]
    estimated_reading_time: int
    
    class Config:
        from_attributes = True


# Model Answer Schemas
class ModelAnswerCreate(BaseModel):
    question_id: UUID
    title: str
    answer_text: str
    key_points: List[str]
    word_count: Optional[int] = None


class ModelAnswerUpdate(BaseModel):
    title: Optional[str] = None
    answer_text: Optional[str] = None
    key_points: Optional[List[str]] = None


class ModelAnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    title: str
    answer_text: str
    key_points: List[str]
    word_count: Optional[int]
    
    class Config:
        from_attributes = True


# Complete Question with Content and Model Answer
class QuestionComplete(BaseModel):
    question: QuestionResponse
    content: Optional[ContentResponse] = None
    model_answer: Optional[ModelAnswerResponse] = None


# Session Schemas
class SessionCreate(BaseModel):
    date: date
    question_id: UUID
    question_number: int = Field(..., ge=1, le=3)


class AnswerUpload(BaseModel):
    session_id: UUID
    answer_type: str = Field(..., pattern="^(before|after)$")
    answer_text: Optional[str] = None
    image_url: Optional[str] = None


class SessionUpdate(BaseModel):
    before_answer_text: Optional[str] = None
    before_answer_image_url: Optional[str] = None
    after_answer_text: Optional[str] = None
    after_answer_image_url: Optional[str] = None
    question_read_time: Optional[int] = None
    before_writing_time: Optional[int] = None
    content_reading_time: Optional[int] = None
    after_writing_time: Optional[int] = None
    model_answer_time: Optional[int] = None
    before_score: Optional[int] = None
    after_score: Optional[int] = None
    improvement: Optional[int] = None
    overall_score: Optional[int] = None
    report_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class SessionResponse(BaseModel):
    id: UUID
    student_id: int
    date: date
    question_id: UUID
    question_number: int
    before_score: Optional[int]
    after_score: Optional[int]
    improvement: Optional[int]
    overall_score: Optional[int]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Activity Tracking
class ActivityCreate(BaseModel):
    session_id: Optional[UUID] = None
    activity_type: str
    activity_data: Optional[Dict[str, Any]] = None


class ActivityResponse(BaseModel):
    id: UUID
    student_id: int
    session_id: Optional[UUID]
    activity_type: str
    activity_data: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Analytics Schemas
class StudentPerformance(BaseModel):
    student_id: int
    student_name: str
    total_drills: int
    average_score: float
    average_improvement: float
    last_drill_date: Optional[date]


class TopicPerformance(BaseModel):
    topic: str
    total_attempts: int
    average_score: float
    average_improvement: float
    difficulty_rating: float


class DailyTrend(BaseModel):
    date: date
    total_students: int
    average_score: float
    average_improvement: float
    completion_rate: float


class AggregateAnalytics(BaseModel):
    total_students: int
    total_drills: int
    average_score: float
    average_improvement: float
    top_performers: List[StudentPerformance]
    struggling_students: List[StudentPerformance]
    topic_performance: List[TopicPerformance]
    daily_trends: List[DailyTrend]


# AI Insights
class CurriculumRecommendation(BaseModel):
    category: str  # content_gap, difficulty_adjustment, new_topic, etc.
    priority: str  # high, medium, low
    description: str
    suggested_action: str


class InsightResponse(BaseModel):
    id: UUID
    date: date
    gs_paper: Optional[str]
    total_students: int
    average_score: float
    common_challenges: List[str]
    high_performing_topics: List[str]
    low_performing_topics: List[str]
    ai_recommendations: List[CurriculumRecommendation]
    
    class Config:
        from_attributes = True


# Bulk Upload
class BulkQuestionUpload(BaseModel):
    questions: List[QuestionCreate]


class BulkUploadResponse(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]

print("DEBUG: app/schemas/drill.py loaded")
