from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime


# Daily Task Schemas
class DailyTaskBase(BaseModel):
    title: str
    completed: bool = False


class DailyTaskCreate(DailyTaskBase):
    date: date


class DailyTaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None


class DailyTaskResponse(DailyTaskBase):
    id: int
    user_id: int
    date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Habit Schemas
class HabitBase(BaseModel):
    name: str
    is_active: bool = True


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class HabitLogResponse(BaseModel):
    date: date
    completed: bool

    model_config = ConfigDict(from_attributes=True)


class HabitResponse(HabitBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    logs: List[HabitLogResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Reflection Schemas
class DailyReflectionBase(BaseModel):
    content: str


class DailyReflectionCreate(DailyReflectionBase):
    date: date


class DailyReflectionUpdate(BaseModel):
    content: str


class DailyReflectionResponse(DailyReflectionBase):
    id: int
    user_id: int
    date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Combined Response for "Today"
class DailyActionSummary(BaseModel):
    date: date
    tasks: List[DailyTaskResponse]
    habits: List[HabitResponse]
    reflection: Optional[DailyReflectionResponse] = None
    
    # Stats
    tasks_completed: int
    total_tasks: int
    streak_days: int
    completion_rate: int  # percentage
