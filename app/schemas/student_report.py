from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class StudentReportBase(BaseModel):
    report_type: str
    report_key: str
    data: Optional[Dict[str, Any]] = None

class StudentReportCreate(StudentReportBase):
    pass

class StudentReportUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None

class StudentReportInDBBase(StudentReportBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentReport(StudentReportInDBBase):
    pass
