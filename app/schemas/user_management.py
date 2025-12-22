"""Schemas for User Management."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


# Data Masking Schemas
class DataMaskingConfigBase(BaseModel):
    role: Optional[str] = None
    user_id: Optional[int] = None
    mask_email: bool = False
    mask_phone: bool = False
    mask_address: bool = False
    mask_financial: bool = False
    custom_masked_fields: Optional[List[str]] = None
    masking_pattern: str = "partial"
    is_active: bool = True


class DataMaskingConfigCreate(DataMaskingConfigBase):
    pass


class DataMaskingConfigUpdate(DataMaskingConfigBase):
    pass


class DataMaskingConfig(DataMaskingConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# User Permission Schemas
class UserPermissionBase(BaseModel):
    can_view_leads: bool = True
    can_edit_leads: bool = False
    can_delete_leads: bool = False
    can_reassign_leads: bool = False
    can_export_leads: bool = False
    can_manage_users: bool = False
    can_view_activity_logs: bool = False
    can_manage_permissions: bool = False
    can_send_emails: bool = True
    can_send_sms: bool = False
    can_make_calls: bool = True
    can_view_reports: bool = True
    can_export_reports: bool = False
    can_view_analytics: bool = False
    can_view_payments: bool = False
    can_process_refunds: bool = False
    custom_permissions: Optional[dict] = None


class UserPermissionCreate(UserPermissionBase):
    user_id: int


class UserPermissionUpdate(UserPermissionBase):
    pass


class UserPermission(UserPermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# User Session Schemas
class UserSessionBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    location: Optional[str] = None


class UserSession(UserSessionBase):
    id: int
    user_id: int
    session_token: str
    is_active: bool
    login_at: datetime
    logout_at: Optional[datetime] = None
    last_activity_at: datetime

    class Config:
        from_attributes = True


# Activity Log Enhanced Schema
class ActivityLogCreate(BaseModel):
    action: str
    details: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ActivityLog(BaseModel):
    id: int
    user_id: int
    action: str
    details: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# User Management Dashboard
class UserWithPermissions(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_banned: bool
    last_login: Optional[datetime] = None
    permissions: Optional[UserPermission] = None
    active_sessions: int = 0

    class Config:
        from_attributes = True


class UserManagementStats(BaseModel):
    total_users: int
    active_users: int
    banned_users: int
    users_by_role: dict
    active_sessions: int
    recent_activities: List[ActivityLog]
