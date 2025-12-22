"""
Enterprise SSO Schemas

Pydantic schemas for SSO models including organizations, configurations,
sessions, and audit logs.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SSOProviderType(str, Enum):
    """Supported SSO provider types"""

    SAML = "SAML"
    OIDC = "OIDC"
    OAUTH = "OAUTH"


# ============================================================================
# Organization Schemas
# ============================================================================


class OrganizationBase(BaseModel):
    """Base organization schema"""

    name: str = Field(..., max_length=200, description="Organization name")
    domain: str = Field(
        ..., max_length=255, description="Primary domain (e.g., company.com)"
    )
    slug: str = Field(..., max_length=100, description="URL-friendly identifier")
    sso_enabled: bool = Field(
        default=False, description="Enable SSO for this organization"
    )
    sso_provider: Optional[str] = Field(
        None, max_length=50, description="SSO provider name"
    )
    sso_enforced: bool = Field(default=False, description="Require SSO for all users")
    is_active: bool = Field(default=True, description="Organization is active")
    max_users: Optional[int] = Field(None, description="Maximum user limit")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Custom settings"
    )


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""

    name: Optional[str] = Field(None, max_length=200)
    domain: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)
    sso_enabled: Optional[bool] = None
    sso_provider: Optional[str] = Field(None, max_length=50)
    sso_enforced: Optional[bool] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization API responses"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SSO Config Schemas
# ============================================================================


class SSOConfigBase(BaseModel):
    """Base SSO configuration schema"""

    organization_id: int
    provider_type: SSOProviderType
    provider_name: Optional[str] = Field(None, max_length=100)

    # SAML fields
    entity_id: Optional[str] = Field(None, max_length=500)
    idp_entity_id: Optional[str] = Field(None, max_length=500)
    sso_url: Optional[str] = Field(None, max_length=500)
    slo_url: Optional[str] = Field(None, max_length=500)
    x509_cert: Optional[str] = None
    certificate_expires_at: Optional[datetime] = None

    # OAuth/OIDC fields
    client_id: Optional[str] = Field(None, max_length=500)
    client_secret: Optional[str] = Field(None, max_length=500)
    authorization_endpoint: Optional[str] = Field(None, max_length=500)
    token_endpoint: Optional[str] = Field(None, max_length=500)
    userinfo_endpoint: Optional[str] = Field(None, max_length=500)
    scopes: List[str] = Field(default_factory=lambda: ["openid", "email", "profile"])

    # Configuration
    attribute_mapping: Dict[str, str] = Field(default_factory=dict)
    role_mapping: Dict[str, str] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)
    jit_enabled: bool = Field(
        default=True, description="Just-in-time user provisioning"
    )
    auto_assign_roles: bool = Field(
        default=True, description="Auto-assign roles from SSO groups"
    )


class SSOConfigCreate(SSOConfigBase):
    """Schema for creating SSO configuration"""

    @validator("provider_type")
    def validate_provider_fields(cls, v, values):
        """Validate required fields based on provider type"""
        # SAML requires: entity_id, idp_entity_id, sso_url, x509_cert
        # OAuth/OIDC requires: client_id, client_secret, authorization_endpoint, token_endpoint
        return v


class SSOConfigUpdate(BaseModel):
    """Schema for updating SSO configuration"""

    provider_type: Optional[SSOProviderType] = None
    provider_name: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[str] = Field(None, max_length=500)
    idp_entity_id: Optional[str] = Field(None, max_length=500)
    sso_url: Optional[str] = Field(None, max_length=500)
    slo_url: Optional[str] = Field(None, max_length=500)
    x509_cert: Optional[str] = None
    certificate_expires_at: Optional[datetime] = None
    client_id: Optional[str] = Field(None, max_length=500)
    client_secret: Optional[str] = Field(None, max_length=500)
    authorization_endpoint: Optional[str] = Field(None, max_length=500)
    token_endpoint: Optional[str] = Field(None, max_length=500)
    userinfo_endpoint: Optional[str] = Field(None, max_length=500)
    scopes: Optional[List[str]] = None
    attribute_mapping: Optional[Dict[str, str]] = None
    role_mapping: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    jit_enabled: Optional[bool] = None
    auto_assign_roles: Optional[bool] = None


class SSOConfigResponse(SSOConfigBase):
    """Schema for SSO config API responses"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_tested_at: Optional[datetime]

    # Hide sensitive data in responses
    client_secret: Optional[str] = Field(None, exclude=True)
    x509_cert: Optional[str] = Field(None, exclude=True)

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SSO Session Schemas
# ============================================================================


class SSOSessionBase(BaseModel):
    """Base SSO session schema"""

    user_id: int
    organization_id: int
    session_id: str
    provider_session_id: Optional[str] = None
    name_id: Optional[str] = None
    provider_type: SSOProviderType
    login_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime


class SSOSessionCreate(SSOSessionBase):
    """Schema for creating SSO session"""

    pass


class SSOSessionResponse(SSOSessionBase):
    """Schema for SSO session API responses"""

    id: int
    created_at: datetime
    last_activity_at: datetime
    logged_out_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SSO Audit Log Schemas
# ============================================================================


class SSOAuditLogBase(BaseModel):
    """Base SSO audit log schema"""

    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    event_type: str = Field(..., max_length=50)
    event_status: Optional[str] = Field(None, max_length=20)
    provider_type: Optional[str] = Field(None, max_length=20)
    ip_address: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None, max_length=500)
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class SSOAuditLogCreate(SSOAuditLogBase):
    """Schema for creating audit log"""

    pass


class SSOAuditLogResponse(SSOAuditLogBase):
    """Schema for audit log API responses"""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Additional DTOs
# ============================================================================


class SSOTestConnectionRequest(BaseModel):
    """Request to test SSO connection"""

    config_id: int
    test_user_email: Optional[str] = Field(
        None, description="Email for test authentication"
    )


class SSOTestConnectionResponse(BaseModel):
    """Response from SSO connection test"""

    success: bool
    provider_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    tested_at: datetime = Field(default_factory=datetime.utcnow)


class SSOLoginRequest(BaseModel):
    """Request to initiate SSO login"""

    organization_slug: str = Field(..., description="Organization identifier")
    redirect_url: Optional[str] = Field(None, description="URL to redirect after login")


class SSOLoginResponse(BaseModel):
    """Response with SSO login redirect URL"""

    login_url: str = Field(..., description="URL to redirect user for authentication")
    provider_type: str
    organization: str


class SSOMetadataResponse(BaseModel):
    """SAML Service Provider metadata"""

    metadata_xml: str = Field(..., description="SP metadata in XML format")
    entity_id: str
    acs_url: str
    slo_url: Optional[str] = None
