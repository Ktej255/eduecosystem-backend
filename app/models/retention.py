"""
FSRS-based Retention System - Database Models
Tracks knowledge decay using Free Spaced Repetition Scheduler (FSRS v4) algorithm.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import math


class UserTopicLog(Base):
    """Track retention for each topic a user learns"""
    __tablename__ = "user_topic_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)  # Links to video/lesson
    topic_type = Column(String(50), default="video")  # video, lesson, meditation
    topic_name = Column(String(255), nullable=True)  # For display
    
    # === FSRS Core Variables ===
    stability = Column(Float, default=1.0)  # S: Days until retention drops to 90%
    difficulty = Column(Float, default=5.0)  # D: Intrinsic difficulty (1-10 scale)
    retrievability = Column(Float, default=1.0)  # R: Current retention probability (0-1)
    
    # === Scores ===
    initial_encoding_score = Column(Float, nullable=True)  # AI comprehension score (0-1)
    last_recall_grade = Column(Integer, nullable=True)  # FSRS grade (1=Again, 2=Hard, 3=Good, 4=Easy)
    total_reviews = Column(Integer, default=0)  # Number of times reviewed
    successful_recalls = Column(Integer, default=0)  # Number of successful recalls
    
    # === Timestamps ===
    learned_at = Column(DateTime(timezone=True), nullable=True)  # When first marked as "learned"
    last_review_date = Column(DateTime(timezone=True), nullable=True)  # Last recall test
    next_due_date = Column(DateTime(timezone=True), nullable=True)  # Scheduled review date
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # === Status ===
    status = Column(String(20), default="new")  # new, learned, reviewing, forgotten, mastered
    is_active = Column(Boolean, default=True)
    
    # === Relationships ===
    user = relationship("User", back_populates="topic_logs")
    
    def calculate_current_retrievability(self) -> float:
        """Calculate current retention based on time elapsed since last review"""
        from datetime import datetime, timezone
        
        if not self.last_review_date or self.stability <= 0:
            return 0.0
        
        now = datetime.now(timezone.utc)
        days_elapsed = (now - self.last_review_date).total_seconds() / 86400
        
        # FSRS Forgetting Curve: R(t) = e^(-t/S)
        return math.exp(-days_elapsed / self.stability)
    
    def calculate_days_until_threshold(self, threshold: float = 0.9) -> int:
        """Calculate days until retention drops below threshold"""
        if self.stability <= 0:
            return 0
        
        # Solve: threshold = e^(-t/S) → t = -S * ln(threshold)
        import math
        return int(-self.stability * math.log(threshold))


class RetentionReview(Base):
    """Log each review/recall attempt"""
    __tablename__ = "retention_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_log_id = Column(Integer, ForeignKey("user_topic_logs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Review data
    review_type = Column(String(30))  # midnight_test, manual_override, feynman_summary
    grade = Column(Integer, nullable=True)  # 1-4 FSRS grade
    score = Column(Float, nullable=True)  # 0-1 AI score (for Feynman)
    
    # FSRS state after this review
    stability_before = Column(Float)
    stability_after = Column(Float)
    retrievability_at_review = Column(Float)
    
    # Content
    user_input = Column(Text, nullable=True)  # Transcript or answer
    ai_feedback = Column(Text, nullable=True)  # AI analysis
    
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    topic_log = relationship("UserTopicLog")


class MidnightTestQuestion(Base):
    """Questions for the evening recall test"""
    __tablename__ = "midnight_test_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    topic_type = Column(String(50), default="video")
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="open")  # open, mcq, true_false
    correct_answer = Column(Text, nullable=True)  # For MCQ/T-F
    key_concepts = Column(Text, nullable=True)  # JSON list of expected concepts
    
    difficulty = Column(Float, default=5.0)  # 1-10
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
