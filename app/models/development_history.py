"""
Database models for Development History and Daily Reports
Tracks development activities, features built, and daily progress reports
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Date, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class DevelopmentLog(Base):
    """
    Tracks development history entries - features developed, challenges faced.
    Used for the Development History page in admin portal.
    """
    __tablename__ = "development_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    batch = Column(String(100), nullable=True, index=True)  # e.g., "Batch 1", "Admin Portal"
    
    # JSON arrays for features and challenges
    features = Column(JSON, default=list)  # List of feature strings
    challenges = Column(JSON, default=list)  # List of challenge strings
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])


class DailyDevReport(Base):
    """
    Daily development reports with batch-wise breakdown.
    Auto-generated or manually created daily summaries.
    """
    __tablename__ = "daily_dev_reports"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    batch = Column(String(100), nullable=True, index=True)
    summary = Column(Text, nullable=True)  # Daily summary text
    
    # Actions taken (JSON array of action objects)
    # Each action: {type: "feature"|"fix"|"enhancement"|"refactor", description: str, files: [str]}
    actions = Column(JSON, default=list)
    
    # Code metrics
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)
    tests_run = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIPlanningSession(Base):
    """
    Stores AI-generated planning sessions for the 7-day planning feature.
    """
    __tablename__ = "ai_planning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    days_analyzed = Column(Integer, default=15)  # How many days of history analyzed
    
    # AI-generated content (JSON)
    plan_items = Column(JSON, default=list)  # 7-day plan items
    insights = Column(JSON, default=list)  # AI insights/recommendations
    
    # Request parameters
    request_params = Column(JSON, default=dict)
    
    # Generation metadata
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    generator = relationship("User", foreign_keys=[generated_by])
