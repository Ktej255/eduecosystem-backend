from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Level configuration constants
GRAPHOTHERAPY_LEVELS = {
    1: {"days": 21, "name": "Foundation", "description": "Building core handwriting habits"},
    2: {"days": 30, "name": "Intermediate", "description": "Improving letter formations"},
    3: {"days": 40, "name": "Advanced", "description": "Word and sentence practice"},
    4: {"days": 90, "name": "Mastery", "description": "Full handwriting transformation"}
}


class DayCompletionBase(BaseModel):
    level: int
    day_number: int
    notes: Optional[str] = None


class DayCompletionCreate(DayCompletionBase):
    pass


class DayCompletionResponse(DayCompletionBase):
    id: int
    progress_id: int
    completed_at: datetime
    upload_url: Optional[str] = None
    upload_filename: Optional[str] = None

    class Config:
        from_attributes = True


class GraphotherapyProgressBase(BaseModel):
    current_level: int = 1
    current_day: int = 1
    total_streak: int = 0


class GraphotherapyProgressCreate(GraphotherapyProgressBase):
    user_id: int


class GraphotherapyProgressResponse(GraphotherapyProgressBase):
    id: int
    user_id: int
    last_practice_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    day_completions: List[DayCompletionResponse] = []

    class Config:
        from_attributes = True


class LevelInfo(BaseModel):
    level: int
    name: str
    description: str
    total_days: int
    completed_days: int
    is_unlocked: bool
    is_current: bool
    is_completed: bool


class LevelDetailResponse(BaseModel):
    level: int
    name: str
    description: str
    total_days: int
    days: List[dict]  # List of day status objects


class DayDetailResponse(BaseModel):
    level: int
    day_number: int
    is_unlocked: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    upload_url: Optional[str] = None
    can_complete_today: bool


class DayCompleteRequest(BaseModel):
    notes: Optional[str] = None


class DayCompleteResponse(BaseModel):
    success: bool
    message: str
    upload_url: Optional[str] = None
    new_streak: int
    level_completed: bool = False
    next_level_unlocked: bool = False


class OverviewResponse(BaseModel):
    current_level: int
    current_day: int
    total_streak: int
    last_practice_date: Optional[datetime] = None
    levels: List[LevelInfo]
    total_days_completed: int
    total_days_remaining: int
