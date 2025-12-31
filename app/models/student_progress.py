
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    student_email = Column(String, index=True, nullable=False)
    segment_key = Column(String, index=True, nullable=False) # e.g. cycle1_day1_part1_seg1
    score = Column(Integer, nullable=False) # e.g. 3
    total_questions = Column(Integer, nullable=False) # e.g. 5
    percentage = Column(Float, nullable=False) # e.g. 60.0
    
    # Metadata
    is_weak_spot = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
