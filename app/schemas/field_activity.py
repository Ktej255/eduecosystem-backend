from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class FieldActivityBase(BaseModel):
    """Base schema for field activity."""
    activity_type: str  # CHECK_IN, CHECK_OUT, MEETING, VISIT, WALK_IN, EVENT, CAMPUS_VISIT
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    lead_id: Optional[int] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    photos: Optional[List[str]] = None
    duration_minutes: Optional[int] = None


class FieldActivityCreate(FieldActivityBase):
    """Schema for creating a field activity."""
    pass


class FieldActivityUpdate(BaseModel):
    """Schema for updating a field activity."""
    notes: Optional[str] = None
    photos: Optional[List[str]] = None
    duration_minutes: Optional[int] = None
    ended_at: Optional[datetime] = None


class FieldActivity(FieldActivityBase):
    """Schema for returning a field activity."""
    id: int
    user_id: int
    route_distance_km: Optional[float] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CheckInRequest(BaseModel):
    """Schema for check-in request."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    """Schema for check-out request."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    route_distance_km: Optional[float] = None


class MeetingLogRequest(BaseModel):
    """Schema for logging a meeting or visit."""
    activity_type: str  # MEETING, VISIT, WALK_IN, EVENT, CAMPUS_VISIT
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    lead_id: Optional[int] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    photos: Optional[List[str]] = None


class FieldActivityDashboard(BaseModel):
    """Dashboard stats for field activities."""
    total_activities_today: int
    check_ins_today: int
    meetings_today: int
    total_distance_km: float
    active_check_in: Optional[FieldActivity] = None
