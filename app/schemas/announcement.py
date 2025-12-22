from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================================
# ANNOUNCEMENT SCHEMAS
# ============================================================================


class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_pinned: bool = False
    send_notification: bool = True
    send_email: bool = False


class AnnouncementCreate(AnnouncementBase):
    """Schema for creating an announcement"""

    course_id: int
    is_published: bool = True


class AnnouncementUpdate(BaseModel):
    """Schema for updating an announcement"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_published: Optional[bool] = None


class AnnouncementInDBBase(AnnouncementBase):
    id: int
    course_id: int
    instructor_id: int
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Announcement(AnnouncementInDBBase):
    """Full announcement schema"""

    instructor_name: Optional[str] = None
    instructor_avatar: Optional[str] = None
    read_count: int = 0
    is_read: bool = False  # For current user


class AnnouncementListItem(BaseModel):
    """Announcement schema for list views"""

    id: int
    title: str
    content: str
    is_pinned: bool
    instructor_name: str
    created_at: datetime
    is_read: bool = False

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# READ TRACKING SCHEMAS
# ============================================================================


class AnnouncementReadCreate(BaseModel):
    """Schema for marking announcement as read"""

    announcement_id: int


class AnnouncementRead(BaseModel):
    id: int
    announcement_id: int
    user_id: int
    read_at: datetime

    model_config = ConfigDict(from_attributes=True)
