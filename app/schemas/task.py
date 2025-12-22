from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.task import TaskType


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType = TaskType.OTHER
    duration_minutes: int = 30
    scheduled_date: datetime
    is_master: bool = False


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    is_completed: Optional[bool] = None


class TaskInDBBase(TaskBase):
    id: int
    is_completed: bool
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class Task(TaskInDBBase):
    pass
