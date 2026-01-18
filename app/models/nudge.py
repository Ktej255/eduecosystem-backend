from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum

class NudgeTriggerType(str, enum.Enum):
    INACTIVITY = "INACTIVITY"         # Student hasn't logged in for X days
    STREAK_DANGER = "STREAK_DANGER"   # Streak about to break
    LOW_SCORE = "LOW_SCORE"           # Quiz score below threshold
    MOOD_DROPPED = "MOOD_DROPPED"     # Negative sentiment detected in reflections

class StudentNudgeWorkflow(Base):
    """Automated nudges to keep students engaged based on their behavior."""
    __tablename__ = "student_nudge_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    # Trigger Rule
    trigger_type = Column(String, nullable=False)  # INACTIVITY, STREAK_DANGER, etc.
    trigger_config = Column(JSON, nullable=True)   # {"days": 3, "threshold": 0.5}
    
    # Action
    message_template = Column(Text, nullable=False)  # "We miss you, {{name}}! Back to Sadhana?"
    action_type = Column(String, default="PUSH")    # PUSH, EMAIL, COINS
    reward_amount = Column(Integer, default=0)       # Bonus coins to incentivize return
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class NudgeHistory(Base):
    """Log of nudges sent to students to prevent spam and track efficacy."""
    __tablename__ = "student_nudge_history"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("student_nudge_workflows.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    action_taken = Column(String)  # PUSH_SENT, EMAIL_SENT, COINS_ADDED
    
    # Engagement Tracking
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True) # Logged in after nudge
