from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CertificateBase(BaseModel):
    student_name: str
    course_title: str
    instructor_name: str


class CertificateCreate(CertificateBase):
    """Schema for creating a certificate"""

    user_id: int
    course_id: int
    enrollment_id: int
    certificate_number: str
    student_email: str
    completion_percentage: float = 100.0
    total_lessons_completed: int = 0
    time_spent_hours: float = 0.0


class CertificateUpdate(BaseModel):
    """Schema for updating a certificate"""

    pdf_url: Optional[str] = None


class Certificate(CertificateBase):
    """Schema for certificate response"""

    id: int
    certificate_number: str
    issued_at: datetime
    pdf_url: Optional[str] = None
    completion_percentage: float
    user_id: int
    course_id: int
    enrollment_id: int
    student_email: str
    time_spent_hours: float = 0.0

    model_config = ConfigDict(from_attributes=True)
