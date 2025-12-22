from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional


class DripSettingBase(BaseModel):
    unlock_type: str
    unlock_date: Optional[datetime] = None
    unlock_after_days: Optional[int] = None
    prerequisite_lesson_id: Optional[int] = None
    is_active: bool = True

    @field_validator("unlock_type")
    @classmethod
    def validate_unlock_type(cls, v):
        if v not in ["date", "sequence", "after_days"]:
            raise ValueError("unlock_type must be one of: date, sequence, after_days")
        return v

    @field_validator("unlock_after_days")
    @classmethod
    def validate_days(cls, v, info):
        if info.data.get("unlock_type") == "after_days" and (v is None or v < 0):
            raise ValueError(
                "unlock_after_days must be a positive integer when unlock_type is after_days"
            )
        return v


class DripSettingCreate(DripSettingBase):
    lesson_id: int


class DripSettingUpdate(BaseModel):
    unlock_type: Optional[str] = None
    unlock_date: Optional[datetime] = None
    unlock_after_days: Optional[int] = None
    prerequisite_lesson_id: Optional[int] = None
    is_active: Optional[bool] = None


class DripSetting(DripSettingBase):
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LessonAccessInfo(BaseModel):
    """Information about lesson access status"""

    has_access: bool
    reason: str
    unlock_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    prerequisite_lesson_id: Optional[int] = None
