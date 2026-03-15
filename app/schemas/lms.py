from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

# --- LMS Assignment Schemas ---

class LMSAssignmentBase(BaseModel):
    title: str
    batch_id: Optional[UUID] = None
    rubric_json: Optional[Any] = None

class LMSAssignmentCreate(LMSAssignmentBase):
    pass

class LMSAssignmentUpdate(BaseModel):
    title: Optional[str] = None
    batch_id: Optional[UUID] = None
    rubric_json: Optional[Any] = None

class LMSAssignment(LMSAssignmentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Student Submission Schemas ---

class StudentSubmissionBase(BaseModel):
    assignment_id: UUID
    content_text: Optional[str] = None
    s3_pdf_url: Optional[str] = None

class StudentSubmissionCreate(StudentSubmissionBase):
    student_id: int

class StudentSubmissionUpdate(BaseModel):
    status: Optional[str] = None
    content_text: Optional[str] = None
    s3_pdf_url: Optional[str] = None

class StudentSubmission(StudentSubmissionBase):
    id: UUID
    student_id: int
    status: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI Evaluation Schemas ---

class AIEvaluationLogBase(BaseModel):
    submission_id: UUID
    ai_score: Optional[float] = None
    ai_feedback_json: Optional[Any] = None
    teacher_approved_score: Optional[float] = None
    status: str = "draft"

class AIEvaluationLogCreate(AIEvaluationLogBase):
    pass

class AIEvaluationLogUpdate(BaseModel):
    ai_score: Optional[float] = None
    ai_feedback_json: Optional[Any] = None
    teacher_approved_score: Optional[float] = None
    status: Optional[str] = None

class AIEvaluationLog(AIEvaluationLogBase):
    id: UUID
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Combined/Detailed Schemas ---

class StudentSubmissionDetailed(StudentSubmission):
    assignment: LMSAssignment
    evaluation_logs: List[AIEvaluationLog] = []
    student_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
