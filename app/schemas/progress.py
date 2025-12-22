from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum


# Progress Schemas
class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LessonProgressBase(BaseModel):
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    time_spent_seconds: Optional[int] = 0
    video_completed_percentage: Optional[float] = 0.0


class LessonProgressUpdate(BaseModel):
    time_spent_seconds: Optional[int] = None
    video_completed_percentage: Optional[float] = None


class LessonProgress(LessonProgressBase):
    id: int
    user_id: int
    lesson_id: int
    completed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseProgress(BaseModel):
    course_id: int
    progress_percentage: float
    completed_lessons: int
    total_lessons: int
    status: str
    completed_at: Optional[datetime] = None


# Certificate Schemas
class CertificateBase(BaseModel):
    student_name: str
    course_title: str
    instructor_name: str


class Certificate(CertificateBase):
    id: int
    certificate_number: str
    issued_at: datetime
    pdf_url: Optional[str] = None
    completion_percentage: float
    completion_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
