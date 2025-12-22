"""Data Masking Configuration Model."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class DataMaskingConfig(Base):
    """Configuration for data masking per role/user."""
    __tablename__ = "data_masking_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Can apply to role or specific user
    role = Column(String, index=True, nullable=True)  # admin, teacher, counselor, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Fields to mask
    mask_email = Column(Boolean, default=False)
    mask_phone = Column(Boolean, default=False)
    mask_address = Column(Boolean, default=False)
    mask_financial = Column(Boolean, default=False)
    
    # Custom field masking (JSON list of field names)
    custom_masked_fields = Column(JSON, nullable=True)
    
    # Masking pattern (e.g., "***", "xxxx", partial like "jo***@email.com")
    masking_pattern = Column(String, default="partial")  # full, partial, hash
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="data_masking_config")


class UserPermission(Base):
    """Granular permissions for users."""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Lead/Application permissions
    can_view_leads = Column(Boolean, default=True)
    can_edit_leads = Column(Boolean, default=False)
    can_delete_leads = Column(Boolean, default=False)
    can_reassign_leads = Column(Boolean, default=False)
    can_export_leads = Column(Boolean, default=False)
    
    # User management permissions
    can_manage_users = Column(Boolean, default=False)
    can_view_activity_logs = Column(Boolean, default=False)
    can_manage_permissions = Column(Boolean, default=False)
    
    # Communication permissions
    can_send_emails = Column(Boolean, default=True)
    can_send_sms = Column(Boolean, default=False)
    can_make_calls = Column(Boolean, default=True)
    
    # Reporting permissions
    can_view_reports = Column(Boolean, default=True)
    can_export_reports = Column(Boolean, default=False)
    can_view_analytics = Column(Boolean, default=False)
    
    # Financial permissions
    can_view_payments = Column(Boolean, default=False)
    can_process_refunds = Column(Boolean, default=False)
    
    # Custom permissions (JSON)
    custom_permissions = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="permissions")


class UserSession(Base):
    """Track user login sessions."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    session_token = Column(String, unique=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_info = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    login_at = Column(DateTime(timezone=True), server_default=func.now())
    logout_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", backref="sessions")
