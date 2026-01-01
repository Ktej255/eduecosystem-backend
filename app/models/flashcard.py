from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True, index=True)
    batch1_segment_key = Column(String(100), nullable=True, index=True) # For Batch 1 videos
    
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    
    difficulty = Column(Float, default=5.0) # 1-10 base difficulty
    source_type = Column(String(50), default="ai_generated") # ai_generated, manual
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lesson = relationship("Lesson", backref="flashcards")

class FlashcardProgress(Base):
    """User-specific progress for a flashcard (FSRS-based)"""
    __tablename__ = "flashcard_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id"), nullable=False, index=True)
    
    # FSRS Core Variables
    stability = Column(Float, default=1.0)
    difficulty = Column(Float, default=5.0)
    
    last_review_date = Column(DateTime(timezone=True), nullable=True)
    next_due_date = Column(DateTime(timezone=True), nullable=True)
    reps = Column(Integer, default=0) # Number of reviews
    lapses = Column(Integer, default=0) # Number of forgotten cases
    
    status = Column(String(20), default="new") # new, learning, reviewing, mastered
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="flashcard_progress")
    flashcard = relationship("Flashcard", backref="user_progress")
