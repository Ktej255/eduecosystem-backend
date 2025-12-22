from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, ConfigDict

# --- Batch Schemas ---
class UPSCBatchBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True

class UPSCBatchCreate(UPSCBatchBase):
    pass

class UPSCBatchUpdate(UPSCBatchBase):
    name: Optional[str] = None
    start_date: Optional[date] = None

class UPSCBatch(UPSCBatchBase):
    id: UUID
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Content Schemas ---
class UPSCContentBase(BaseModel):
    content_type: str # one_pager, model_answer, pdf
    title: Optional[str] = None
    content_text: Optional[str] = None
    file_url: Optional[str] = None
    microtopics: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    current_affairs: Optional[List[str]] = None

class UPSCContentCreate(UPSCContentBase):
    question_id: UUID

class UPSCContentUpdate(UPSCContentBase):
    content_type: Optional[str] = None

class UPSCContent(UPSCContentBase):
    id: UUID
    question_id: UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Question Schemas ---
class UPSCQuestionBase(BaseModel):
    question_number: int
    title: str
    question_text: str
    marks: int
    subject: str
    topic: Optional[str] = None
    microtopics: List[str]
    keywords: Optional[List[str]] = None
    pyq_reference: Optional[str] = None

class UPSCQuestionCreate(UPSCQuestionBase):
    plan_id: UUID

class UPSCQuestionUpdate(UPSCQuestionBase):
    question_number: Optional[int] = None
    title: Optional[str] = None
    question_text: Optional[str] = None
    marks: Optional[int] = None
    subject: Optional[str] = None
    microtopics: Optional[List[str]] = None

class UPSCQuestion(UPSCQuestionBase):
    id: UUID
    plan_id: UUID
    content: List[UPSCContent] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Plan Schemas ---
class UPSCPlanBase(BaseModel):
    title: str
    plan_type: str # monthly, weekly, daily
    start_date: date
    end_date: date
    sequence_order: int
    plan_data: Optional[Dict[str, Any]] = None

class UPSCPlanCreate(UPSCPlanBase):
    batch_id: UUID
    parent_plan_id: Optional[UUID] = None
    ai_generated: bool = False

class UPSCPlanUpdate(UPSCPlanBase):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sequence_order: Optional[int] = None

class UPSCPlan(UPSCPlanBase):
    id: UUID
    batch_id: UUID
    parent_plan_id: Optional[UUID] = None
    ai_generated: bool
    approved_at: Optional[datetime] = None
    questions: List[UPSCQuestion] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Drill Schemas ---
class UPSCDrillBase(BaseModel):
    scheduled_at: datetime
    status: str = "scheduled"

class UPSCDrillCreate(UPSCDrillBase):
    batch_id: UUID
    plan_id: UUID

class UPSCDrill(UPSCDrillBase):
    id: UUID
    batch_id: UUID
    plan_id: UUID
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Attempt Schemas ---
class UPSCAttemptBase(BaseModel):
    attempt_type: str # before, after
    answer_text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    word_count: Optional[int] = None
    time_taken_seconds: Optional[int] = None

class UPSCAttemptCreate(UPSCAttemptBase):
    question_id: UUID
    drill_session_id: Optional[UUID] = None

class UPSCAttempt(UPSCAttemptBase):
    id: UUID
    student_id: UUID
    question_id: UUID
    ocr_confidence: Optional[float] = None
    submitted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Report Schemas ---
class UPSCReportBase(BaseModel):
    coverage_before: Optional[float] = None
    similarity_before: Optional[float] = None
    estimated_marks_before: Optional[float] = None
    coverage_after: Optional[float] = None
    similarity_after: Optional[float] = None
    estimated_marks_after: Optional[float] = None
    missed_points: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    tone_feedback: Optional[str] = None

class UPSCReport(UPSCReportBase):
    id: UUID
    student_id: UUID
    question_id: UUID
    attempt_before_id: Optional[UUID] = None
    attempt_after_id: Optional[UUID] = None
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- AI Generation Schemas ---
class PlanGenerationRequest(BaseModel):
    batch_id: UUID
    subject: str
    start_date: date
    total_days: int
    questions_per_day: int = 3
    topics: List[str]

class StartDrillRequest(BaseModel):
    plan_id: UUID
    question_number: int

class StartDrillResponse(BaseModel):
    session_id: UUID
    question: UPSCQuestion
    current_step: Dict[str, Any]
    timer_config: Dict[str, int]

class PlanStatusResponse(BaseModel):
    plan_id: UUID
    is_locked: bool
    completion_percentage: float
    unlocked_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class StudentDashboardResponse(BaseModel):
    total_days_completed: int
    current_streak: int
    next_drill: Optional[Dict[str, Any]] = None
    recent_reports: List[UPSCReport] = []

