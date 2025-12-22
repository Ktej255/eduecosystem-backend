from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class GraphotherapyProgress(Base):
    """Track overall graphotherapy progress for a student"""
    __tablename__ = "graphotherapy_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_level = Column(Integer, default=1)  # 1-4
    current_day = Column(Integer, default=1)  # Current day in current level
    total_streak = Column(Integer, default=0)  # Overall streak count
    last_practice_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="graphotherapy_progress")
    day_completions = relationship("GraphotherapyDayCompletion", back_populates="progress", cascade="all, delete-orphan")


class GraphotherapyDayCompletion(Base):
    """Track individual day completions with uploads"""
    __tablename__ = "graphotherapy_day_completions"

    id = Column(Integer, primary_key=True, index=True)
    progress_id = Column(Integer, ForeignKey("graphotherapy_progress.id"), nullable=False)
    level = Column(Integer, nullable=False)  # 1-4
    day_number = Column(Integer, nullable=False)  # Day within the level
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    upload_url = Column(String(500), nullable=True)  # URL to the uploaded image
    upload_filename = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)  # Optional notes from student

    # Relationships
    progress = relationship("GraphotherapyProgress", back_populates="day_completions")


# Level configuration
GRAPHOTHERAPY_LEVELS = {
    1: {"days": 21, "name": "Foundation", "description": "Building core handwriting habits"},
    2: {"days": 30, "name": "Intermediate", "description": "Improving letter formations"},
    3: {"days": 40, "name": "Advanced", "description": "Word and sentence practice"},
    4: {"days": 90, "name": "Mastery", "description": "Full handwriting transformation"}
}
