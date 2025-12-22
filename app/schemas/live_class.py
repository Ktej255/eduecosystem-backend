from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.live_class import LiveClassStatus


# Base schemas
class LiveClassBase(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None
    platform: str = "zoom"


class LiveClassCreate(LiveClassBase):
    course_id: int


class LiveClassUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[LiveClassStatus] = None
    recording_url: Optional[str] = None
    recording_available: Optional[bool] = None


class LiveClass(LiveClassBase):
    id: int
    course_id: int
    status: LiveClassStatus
    recording_url: Optional[str] = None
    recording_available: bool
    instructor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Attendance schemas
class AttendanceBase(BaseModel):
    live_class_id: int


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    left_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    asked_questions: Optional[int] = None
    reactions_count: Optional[int] = None


class Attendance(AttendanceBase):
    id: int
    student_id: int
    joined_at: datetime
    left_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    asked_questions: int
    reactions_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Extended schemas with relationships
class LiveClassWithAttendance(LiveClass):
    attendance_count: int = 0
    attendance_records: List[Attendance] = []


class LiveClassList(BaseModel):
    """Paginated list of live classes"""

    items: List[LiveClass]
    total: int
    page: int
    page_size: int
