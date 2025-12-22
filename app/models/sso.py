"""
Enterprise SSO Models

Models for Single Sign-On (SSO) with SAML 2.0 and OAuth/OIDC support.
Supports organization management, SSO configuration, and session tracking.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class SSOProviderType(str, enum.Enum):
    """Supported SSO provider types"""

    SAML = "saml"
    OIDC = "oidc"
    OAUTH = "oauth"


class Organization(Base):
    """
    Enterprise organization with SSO capabilities.
    """

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    domain = Column(
        String(255), unique=True, nullable=False, index=True
    )  # e.g., "company.com"
    slug = Column(
        String(100), unique=True, nullable=False, index=True
    )  # URL-friendly name

    # SSO settings
    sso_enabled = Column(Boolean, default=False)
    sso_provider = Column(String(50))  # 'azure_ad', 'google_workspace', 'okta', etc.
    sso_enforced = Column(Boolean, default=False)  # Require SSO for all users

    # Organization settings
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer)  # User limit for subscription
    settings = Column(JSON, default={})  # Custom org settings

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    sso_configs = relationship(
        "SSOConfig", back_populates="organization", cascade="all, delete-orphan"
    )
    sso_sessions = relationship("SSOSession", back_populates="organization")


class SSOConfig(Base):
    """
    SSO provider configuration for an organization.
    """

    __tablename__ = "sso_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    # Provider details
    provider_type = Column(
        Enum(SSOProviderType), nullable=False
    )  # 'saml', 'oidc', 'oauth'
    provider_name = Column(String(100))  # 'Azure AD', 'Google Workspace', etc.

    # SAML-specific fields
    entity_id = Column(String(500))  # SP entity ID
    idp_entity_id = Column(String(500))  # IdP entity ID
    sso_url = Column(String(500))  # IdP SSO URL
    slo_url = Column(String(500))  # Single Logout URL (optional)
    x509_cert = Column(Text)  # IdP certificate for signature validation
    certificate_expires_at = Column(DateTime(timezone=True))  # Certificate expiry

    # OAuth/OIDC-specific fields
    client_id = Column(String(500))
    client_secret = Column(String(500))  # Encrypted in production
    authorization_endpoint = Column(String(500))
    token_endpoint = Column(String(500))
    userinfo_endpoint = Column(String(500))
    scopes = Column(JSON, default=["openid", "email", "profile"])  # OAuth scopes

    # User attribute mapping
    attribute_mapping = Column(JSON, default={})
    """
    Maps SSO attributes to user fields:
    {
        "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        "first_name": "given_name",
        "last_name": "family_name",
        "groups": "groups"
    }
    """

    # Role mapping from SSO groups
    role_mapping = Column(JSON, default={})
    """
    Maps SSO groups to platform roles:
    {
        "LMS-Instructors": "instructor",
        "LMS-Students": "student",
        "LMS-Admins": "admin"
    }
    """

    # Configuration settings
    settings = Column(JSON, default={})  # Additional provider-specific settings
    is_active = Column(Boolean, default=True)

    # JIT provisioning settings
    jit_enabled = Column(Boolean, default=True)  # Just-in-time user creation
    auto_assign_roles = Column(Boolean, default=True)  # Auto-assign roles from groups

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_tested_at = Column(DateTime(timezone=True))  # Last successful test

    # Relationships
    organization = relationship("Organization", back_populates="sso_configs")


class SSOSession(Base):
    """
    Track active SSO sessions for logout and audit purposes.
    """

    __tablename__ = "sso_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )

    # Session identifiers
    session_id = Column(
        String(255), unique=True, nullable=False, index=True
    )  # Our session ID
    provider_session_id = Column(
        String(255), index=True
    )  # Provider's session ID (for SLO)
    name_id = Column(String(500))  # SAML NameID (for logout)

    # Session metadata
    provider_type = Column(Enum(SSOProviderType), nullable=False)
    login_method = Column(String(50))  # 'saml', 'oidc', 'azure_ad', etc.
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    logged_out_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User")
    organization = relationship("Organization", back_populates="sso_sessions")


class SSOAuditLog(Base):
    """
    Audit log for SSO events (logins, logouts, configuration changes).
    """

    __tablename__ = "sso_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)

    # Event details
    event_type = Column(
        String(50), nullable=False, index=True
    )  # 'login', 'logout', 'config_change', etc.
    event_status = Column(String(20))  # 'success', 'failure', 'error'
    provider_type = Column(String(20))  # 'saml', 'oidc', etc.

    # Event data
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    details = Column(JSON)  # Additional event details
    error_message = Column(Text)  # If event failed

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
