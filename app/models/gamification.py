from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base

class ActivityType(str, enum.Enum):
    LOGIN = "login"
    MEDITATION = "meditation" 
    DRILL = "drill"
    FLASHCARD = "flashcard"

class Streak(Base):
    """Tracks streak for specific activities"""
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String, index=True) # e.g., 'meditation', 'login'
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="streaks")

class Squad(Base):
    """Group of users for team challenges"""
    __tablename__ = "squads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    members = relationship("SquadMember", back_populates="squad")
    created_by = relationship("User", foreign_keys=[created_by_id])

class SquadMember(Base):
    """Membership in a squad"""
    __tablename__ = "squad_members"

    id = Column(Integer, primary_key=True, index=True)
    squad_id = Column(Integer, ForeignKey("squads.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, default="member") # member, leader
    
    squad = relationship("Squad", back_populates="members")
    user = relationship("User", backref="squad_memberships")
