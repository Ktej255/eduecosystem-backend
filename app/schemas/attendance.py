from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AttendanceBase(BaseModel):
    session_type: str
    timestamp: Optional[datetime] = None
    mode: Optional[str] = "live"

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    user_id: int
    is_present: bool

    class Config:
        from_attributes = True
