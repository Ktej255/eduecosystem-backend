from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# Assignment Schemas
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    max_points: float = 100.0
    due_date: Optional[datetime] = None
    allow_late_submission: bool = True
    late_penalty_per_day: float = 0.0
    is_published: bool = False
    file_upload_required: bool = True
    allowed_file_types: List[str] = []
    max_file_size_mb: int = 50


class AssignmentCreate(AssignmentBase):
    course_id: int
    lesson_id: Optional[int] = None


class AssignmentUpdate(AssignmentBase):
    pass


class Assignment(AssignmentBase):
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Submission Schemas
class SubmissionBase(BaseModel):
    notes: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    assignment_id: int
    submitted_files: List[str] = []


class SubmissionUpdate(BaseModel):
    grade: Optional[float] = None
    feedback: Optional[str] = None
    status: Optional[str] = None


class Submission(SubmissionBase):
    id: int
    assignment_id: int
    user_id: int
    submitted_files: List[str] = []
    grade: Optional[float] = None
    feedback: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionWithUser(Submission):
    user: Optional[dict] = None  # Will contain user info (id, name, email)

    model_config = ConfigDict(from_attributes=True)
