"""
Meditation Session System - Pydantic Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MeditationProcessBase(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 1
    duration_minutes: int = 5
    level: int = 1


class MeditationProcessCreate(MeditationProcessBase):
    pass


class MeditationProcessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    duration_minutes: Optional[int] = None
    video_url: Optional[str] = None
    is_active: Optional[bool] = None


class MeditationProcessResponse(MeditationProcessBase):
    id: int
    video_url: Optional[str] = None
    video_filename: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class MeditationProgressResponse(BaseModel):
    id: int
    user_id: int
    current_level: int
    current_day: int
    total_streak: int
    preferred_session: str
    last_practice_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeditationDayOverview(BaseModel):
    """Overview of processes for a specific day"""
    level: int
    day_number: int
    total_processes: int
    is_unlock_day: bool  # Whether new processes are introduced today
    new_process_start: Optional[int] = None  # First new process number (if unlock day)
    new_process_end: Optional[int] = None    # Last new process number (if unlock day)
    processes: List[MeditationProcessResponse]
    completed_processes: List[int]  # IDs of completed processes
    is_day_completed: bool


class MeditationLevelInfo(BaseModel):
    """Info about a meditation level"""
    level: int
    name: str
    description: str
    total_days: int
    completed_days: int
    is_unlocked: bool
    is_current: bool
    is_completed: bool


class MeditationOverviewResponse(BaseModel):
    """Overall meditation progress overview"""
    current_level: int
    current_day: int
    total_streak: int
    last_practice_date: Optional[datetime] = None
    preferred_session: str
    levels: List[MeditationLevelInfo]
    total_days_completed: int
    total_days_remaining: int
    # Today's session info
    todays_processes: int
    is_unlock_day: bool


class MeditationDayInfo(BaseModel):
    """Info about a specific day in the calendar"""
    day_number: int
    is_unlocked: bool
    is_completed: bool
    completed_at: Optional[str] = None
    unlock_date: Optional[str] = None
    processes_count: int


class MeditationLevelDetailResponse(BaseModel):
    """Detailed view of a level with all days"""
    level: int
    name: str
    description: str
    total_days: int
    days: List[MeditationDayInfo]


class ProcessCompleteRequest(BaseModel):
    watched_video: bool = False


class ProcessCompleteResponse(BaseModel):
    success: bool
    message: str
    process_id: int
    all_processes_done: bool


class DayCompleteRequest(BaseModel):
    session_type: str = "morning"  # morning/night
    notes: Optional[str] = None


class DayCompleteResponse(BaseModel):
    success: bool
    message: str
    new_streak: int
    level_completed: bool = False
    next_level_unlocked: bool = False
