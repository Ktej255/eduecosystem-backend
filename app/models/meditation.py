"""
Meditation Session System - Database Models
4-Level System with Progressive Processes
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


# Level configuration
MEDITATION_LEVELS = {
    1: {"days": 60, "name": "Foundation", "description": "Building daily meditation habit"},
    2: {"days": 60, "name": "Intermediate", "description": "Deepening your practice"},
    3: {"days": 60, "name": "Advanced", "description": "Advanced meditation techniques"},
    4: {"days": 60, "name": "Mastery", "description": "Complete mastery of meditation"}
}

# Process unlock schedule: Every 7 days, 3 new processes are added
# Day 1: processes 1-3, Day 8: 4-6, Day 15: 7-9, Day 22: 10-12
PROCESS_UNLOCK_INTERVAL = 7  # Days between new process additions
PROCESSES_PER_UNLOCK = 3     # Number of new processes added each unlock


class MeditationProcess(Base):
    """Store meditation processes with videos"""
    __tablename__ = "meditation_processes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=1)  # Order in which processes appear
    video_url = Column(String(500), nullable=True)  # URL to explanation video
    video_filename = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, default=5)  # Estimated duration
    level = Column(Integer, default=1)  # Which level this process belongs to
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MeditationProgress(Base):
    """Track overall meditation progress for a student"""
    __tablename__ = "meditation_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_level = Column(Integer, default=1)
    current_day = Column(Integer, default=1)
    total_streak = Column(Integer, default=0)
    preferred_session = Column(String(20), default="morning")  # morning/night
    last_practice_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="meditation_progress")
    day_completions = relationship("MeditationDayCompletion", back_populates="progress", cascade="all, delete-orphan")


class MeditationDayCompletion(Base):
    """Track individual day completions"""
    __tablename__ = "meditation_day_completions"

    id = Column(Integer, primary_key=True, index=True)
    progress_id = Column(Integer, ForeignKey("meditation_progress.id"), nullable=False)
    level = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)
    session_type = Column(String(20), default="morning")  # morning/night
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    total_duration_minutes = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    # Relationships
    progress = relationship("MeditationProgress", back_populates="day_completions")
    process_completions = relationship("MeditationProcessCompletion", back_populates="day_completion", cascade="all, delete-orphan")


class MeditationProcessCompletion(Base):
    """Track individual process completions within a day"""
    __tablename__ = "meditation_process_completions"

    id = Column(Integer, primary_key=True, index=True)
    day_completion_id = Column(Integer, ForeignKey("meditation_day_completions.id"), nullable=False)
    process_id = Column(Integer, ForeignKey("meditation_processes.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    watched_video = Column(Boolean, default=False)  # Whether explanation video was watched

    # Relationships
    day_completion = relationship("MeditationDayCompletion", back_populates="process_completions")
    process = relationship("MeditationProcess")


# Keep backward compatibility with old model
class MeditationSession(Base):
    """Legacy model - kept for compatibility"""
    __tablename__ = "meditation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    minutes_listened = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="meditation_sessions")


def get_processes_for_day(day_number: int) -> tuple:
    """
    Calculate which processes are available for a given day.
    Returns (start_process, end_process, is_unlock_day)
    
    Day 1: processes 1-3 (new)
    Day 2-7: processes 1-3
    Day 8: processes 1-6 (3 new)
    Day 9-14: processes 1-6
    Day 15: processes 1-9 (3 new)
    Day 16-21: processes 1-9
    Day 22: processes 1-12 (3 new)
    Day 23-28: processes 1-12
    """
    if day_number < 1:
        return (0, 0, False)
    
    # Calculate how many unlock cycles have passed
    # Day 1 = cycle 0, Day 8 = cycle 1, Day 15 = cycle 2, etc.
    unlock_cycle = (day_number - 1) // PROCESS_UNLOCK_INTERVAL
    
    # Calculate total processes available
    total_processes = (unlock_cycle + 1) * PROCESSES_PER_UNLOCK
    
    # Cap at 12 processes for Day 28 (4 unlock cycles: Day 1, 8, 15, 22)
    max_processes = 12
    total_processes = min(total_processes, max_processes)
    
    # Check if this is an unlock day (Day 1, 8, 15, 22, etc.)
    is_unlock_day = (day_number - 1) % PROCESS_UNLOCK_INTERVAL == 0
    
    return (1, total_processes, is_unlock_day)


def get_new_processes_for_day(day_number: int) -> tuple:
    """
    Get the range of NEW processes introduced on a specific day.
    Returns (start, end) or (0, 0) if no new processes.
    """
    if day_number < 1:
        return (0, 0)
    
    # Check if this is an unlock day
    is_unlock_day = (day_number - 1) % PROCESS_UNLOCK_INTERVAL == 0
    
    if not is_unlock_day:
        return (0, 0)
    
    # Calculate which cycle this is
    unlock_cycle = (day_number - 1) // PROCESS_UNLOCK_INTERVAL
    
    # Calculate process range for this unlock
    start_process = unlock_cycle * PROCESSES_PER_UNLOCK + 1
    end_process = start_process + PROCESSES_PER_UNLOCK - 1
    
    # Cap at 12
    if start_process > 12:
        return (0, 0)
    end_process = min(end_process, 12)
    
    return (start_process, end_process)
