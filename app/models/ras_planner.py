from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class RASPlan(Base):
    """Stores generated daily study plans for students"""
    __tablename__ = "ras_plans"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    date = Column(Date, index=True)
    day_number = Column(Integer)
    slots = Column(JSON)  # Stores slot structure and topic assignments
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RASTopicProgress(Base):
    """Tracks completion and recall mastery for specific topics"""
    __tablename__ = "ras_topic_progress"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    topic_id = Column(String, index=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    recall_score = Column(Integer, nullable=True) # 0-100
    method = Column(String, nullable=True) # manual, ai_verification
    last_attempt_at = Column(DateTime, default=datetime.utcnow)

class RASRecording(Base):
    """Stores student recording submissions and AI feedback"""
    __tablename__ = "ras_recordings"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    topic_id = Column(String, index=True)
    recording_url = Column(String, nullable=True)
    explanation_text = Column(String, nullable=True)
    recall_score = Column(Integer)
    duration = Column(Integer) # in seconds
    feedback = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
