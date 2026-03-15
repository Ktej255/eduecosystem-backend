from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserSessionBase(BaseModel):
    is_active: bool = True

class UserSessionCreate(UserSessionBase):
    pass

class UserSessionUpdate(BaseModel):
    last_heartbeat: datetime
    duration_seconds: int
    is_active: bool = True
    end_time: Optional[datetime] = None

class UserSession(UserSessionBase):
    id: int
    user_id: int
    start_time: datetime
    last_heartbeat: datetime
    end_time: Optional[datetime]
    duration_seconds: int

    class Config:
        from_attributes = True

class HeartbeatResponse(BaseModel):
    session_id: int
    duration_seconds: int
    status: str
