from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(String, nullable=True, index=True)
    topic_name = Column(String, nullable=True)
    subject_id = Column(String, nullable=True)
    subject_name = Column(String, nullable=True)
    
    session_type = Column(String, nullable=False) # study_25, study_45, explanation_5, explanation_10, revision_25
    
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # AI Analysis fields
    audio_transcript = Column(String, nullable=True)
    ai_analysis = Column(JSON, nullable=True) # JSON blob from Gemini
    comprehension_score = Column(Integer, nullable=True) # 0-100
    
    # Metadata
    cycle_number = Column(Integer, default=1)
    phase_number = Column(Integer, default=1)

    # Relationships
    user = relationship("User", backref="study_sessions")
