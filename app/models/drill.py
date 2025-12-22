"""
Database models for Drill System
Includes questions, content, sessions, and activity tracking
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Date, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base


class DrillQuestion(Base):
    """Questions for daily drill"""
    __tablename__ = "drill_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gs_paper = Column(String(10), nullable=False, index=True)  # GS1, GS2, GS3, GS4
    topic = Column(String(255), nullable=False, index=True)
    sub_topic = Column(String(255))
    question_text = Column(Text, nullable=False)
    key_points = Column(JSON)  # List of key points to cover
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    content = relationship("DrillContent", back_populates="question", uselist=False)
    model_answer = relationship("DrillModelAnswer", back_populates="question", uselist=False)
    sessions = relationship("DrillSession", back_populates="question")


class DrillContent(Base):
    """Study content for questions"""
    __tablename__ = "drill_content"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("drill_questions.id"), unique=True)
    
    title = Column(String(255), nullable=False)
    sections = Column(JSON, nullable=False)  # [{heading: str, text: str}]
    estimated_reading_time = Column(Integer, default=60)  # minutes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = relationship("DrillQuestion", back_populates="content")


class DrillModelAnswer(Base):
    """Model answers for questions"""
    __tablename__ = "drill_model_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(36), ForeignKey("drill_questions.id"), unique=True)
    
    title = Column(String(255), nullable=False)
    answer_text = Column(Text, nullable=False)
    key_points = Column(JSON)  # List of key points
    word_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = relationship("DrillQuestion", back_populates="model_answer")


class DrillSession(Base):
    """Student drill sessions"""
    __tablename__ = "drill_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("drill_questions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)  # 1, 2, or 3
    
    # Answers
    before_answer_text = Column(Text)
    before_answer_image_url = Column(String(500))
    after_answer_text = Column(Text)
    after_answer_image_url = Column(String(500))
    
    # Timing data (in seconds)
    question_read_time = Column(Integer)
    before_writing_time = Column(Integer)
    content_reading_time = Column(Integer)
    after_writing_time = Column(Integer)
    model_answer_time = Column(Integer)
    
    # Scores from AI
    before_score = Column(Integer)
    after_score = Column(Integer)
    improvement = Column(Integer)
    overall_score = Column(Integer)
    
    # Full report from AI
    report_data = Column(JSON)
    
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    question = relationship("DrillQuestion", back_populates="sessions")
    activities = relationship("StudentActivity", back_populates="session")


class DrillDailySummary(Base):
    """Daily summary for all 3 questions"""
    __tablename__ = "drill_daily_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    overall_score = Column(Integer)
    average_improvement = Column(Integer)
    total_time_spent = Column(Integer)  # minutes
    
    # Question-wise scores
    question_scores = Column(JSON)  # {q1: {before, after, improvement}, ...}
    
    # Comparison with yesterday
    comparison_data = Column(JSON)
    
    # AI insights
    strengths = Column(JSON) # List of strings
    challenges = Column(JSON) # List of strings
    recommendations = Column(JSON) # List of strings
    insights = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])


class StudentActivity(Base):
    """Track all student activities"""
    __tablename__ = "student_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("drill_sessions.id"), index=True)
    
    activity_type = Column(String(50), nullable=False)  # click, step_complete, timer_expire, etc.
    activity_data = Column(JSON)  # Additional data about the activity
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    session = relationship("DrillSession", back_populates="activities")


class CurriculumInsight(Base):
    """AI-generated curriculum insights for admins"""
    __tablename__ = "curriculum_insights"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False, index=True)
    gs_paper = Column(String(10), index=True)
    
    # Aggregate metrics
    total_students = Column(Integer)
    average_score = Column(Float)
    common_challenges = Column(JSON) # List of strings
    high_performing_topics = Column(JSON) # List of strings
    low_performing_topics = Column(JSON) # List of strings
    
    # AI recommendations
    ai_recommendations = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
