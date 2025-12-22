from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enum for API"""

    # Academic
    COURSE_ENROLLED = "course_enrolled"
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_GRADED = "assignment_graded"
    CERTIFICATE_ISSUED = "certificate_issued"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"

    # Instructor
    STUDENT_ENROLLED = "student_enrolled"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    COURSE_REVIEW = "course_review"

    # Social
    FRIEND_REQUEST = "friend_request"
    GROUP_INVITATION = "group_invitation"
    MENTION = "mention"

    # System
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationBase(BaseModel):
    """Base notification schema"""

    type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""

    user_id: int


class NotificationUpdate(BaseModel):
    """Schema for updating notification"""

    is_read: Optional[bool] = None


class Notification(NotificationBase):
    """Complete notification schema"""

    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationList(BaseModel):
    """Paginated notification list"""

    notifications: list[Notification]
    total: int
    unread_count: int


class UnreadCount(BaseModel):
    """Unread notification count"""

    count: int


# ============================================================================
# EMAIL NOTIFICATION SCHEMAS
# ============================================================================


class EmailPreferenceBase(BaseModel):
    """Base schema for email preferences"""

    enrollment_enabled: bool = True
    assignment_enabled: bool = True
    quiz_enabled: bool = True
    certificate_enabled: bool = True
    announcement_enabled: bool = True
    review_enabled: bool = True
    course_update_enabled: bool = True
    general_enabled: bool = True
    all_emails_enabled: bool = True


class EmailPreferenceUpdate(EmailPreferenceBase):
    """Schema for updating email preferences"""

    pass


class EmailPreference(EmailPreferenceBase):
    """Complete email preference schema"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailTemplateBase(BaseModel):
    """Base schema for email templates"""

    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=200)
    body_html: str
    body_text: Optional[str] = None
    variables: list[str] = Field(default_factory=list)
    notification_type: str


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating email templates"""

    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating email templates"""

    display_name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None


class EmailTemplate(EmailTemplateBase):
    """Complete email template schema"""

    id: int
    is_system: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailLogBase(BaseModel):
    """Base schema for email logs"""

    recipient_email: str
    subject: str
    status: str


class EmailLog(EmailLogBase):
    """Complete email log schema"""

    id: int
    user_id: int
    template_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendEmailRequest(BaseModel):
    """Schema for sending test emails"""

    recipient_email: str
    template_name: str
    variables: Optional[Dict[str, Any]] = None
