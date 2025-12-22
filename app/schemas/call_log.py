from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CallLogBase(BaseModel):
    """Base schema for call log."""
    lead_id: int
    call_type: str  # OUTGOING, INCOMING, MISSED
    phone_number: Optional[str] = None
    duration_seconds: Optional[int] = 0
    outcome: Optional[str] = None  # CONNECTED, NO_ANSWER, BUSY, VOICEMAIL, WRONG_NUMBER
    notes: Optional[str] = None


class CallLogCreate(CallLogBase):
    """Schema for creating a call log."""
    pass


class CallLogUpdate(BaseModel):
    """Schema for updating a call log."""
    duration_seconds: Optional[int] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    call_ended_at: Optional[datetime] = None


class CallLog(CallLogBase):
    """Schema for returning a call log."""
    id: int
    user_id: int
    call_started_at: datetime
    call_ended_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuickCallRequest(BaseModel):
    """Schema for initiating a quick call from the app."""
    lead_id: int
    phone_number: str


class CallLogSummary(BaseModel):
    """Summary of calls for a user or lead."""
    total_calls: int
    connected_calls: int
    missed_calls: int
    total_duration_minutes: float
    average_duration_seconds: float
