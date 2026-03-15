from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AttendanceBase(BaseModel):
    session_type: str
    timestamp: Optional[datetime] = None
    mode: Optional[str] = "live"
    duration_minutes: Optional[int] = 0
    is_late: Optional[bool] = False

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    user_id: int
    is_present: bool
    # We'll add user details for the admin view
    user: Optional[dict] = None 

    class Config:
        from_attributes = True
