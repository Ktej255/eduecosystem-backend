from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Skill(Base):
    """
    Registry of the 36 Skills (Financial, Digital, Mindset, Personal)
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(String(50), unique=True, index=True) # e.g., 'fin-1', 'dig-2'
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False) # financial, digital, mindset, personal
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    
    # Unlocking criteria (JSON logic or simple strings)
    unlock_requirement_type = Column(String(50), nullable=True) # academy_milestone, streak, payment
    unlock_requirement_value = Column(String(255), nullable=True) # e.g., 'economy-complete', '7-day-streak'
    
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="INR")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StudentSkillProgress(Base):
    """
    Track student progress on specific skills
    """
    __tablename__ = "student_skill_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    status = Column(String(20), default="locked") # locked, unlocked, in-progress, mastered
    mastery_percentage = Column(Integer, default=0)
    
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    mastered_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="skill_progress")
    skill = relationship("Skill")
