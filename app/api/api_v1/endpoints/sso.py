"""
SSO (Single Sign-On) API Endpoints

API endpoints for Enterprise SSO authentication, organization management, and configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
import secrets
from datetime import timedelta

from app.api import deps
from app.models.user import User
from app.models.sso import Organization, SSOConfig, SSOAuditLog, SSOProviderType
from app.services.sso_service import SSOService
from app.core.config import settings

# Import protocol services
# We handle imports inside functions or here if available
try:
    from app.services.saml_service import SAMLService, prepare_flask_request
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False

try:
    from app.services.oauth_service import OAuthService
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

router = APIRouter()

# --- Request/Response Schemas ---

class OrganizationCreate(BaseModel):
    name: str
    domain: str
    slug: str
    sso_enabled: bool = False

class OrganizationResponse(BaseModel):
    id: int
    name: str
    domain: str
    slug: str
    sso_enabled: bool
    sso_provider: Optional[str]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class SSOConfigCreate(BaseModel):
    provider_type: SSOProviderType
    provider_name: str
    # SAML fields
    entity_id: Optional[str] = None
    idp_entity_id: Optional[str] = None
    sso_url: Optional[str] = None
    x509_cert: Optional[str] = None
    # OAuth fields
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    scopes: Optional[List[str]] = None
    # Configuration
    attribute_mapping: Optional[dict] = None
    role_mapping: Optional[dict] = None
    jit_enabled: bool = True
    auto_assign_roles: bool = True

class SSOConfigResponse(BaseModel):
    id: int
    organization_id: int
    provider_type: str
    provider_name: str
    is_active: bool
    jit_enabled: bool
    
    model_config = ConfigDict(from_attributes=True)

class SSOLoginRequest(BaseModel):
    organization_slug: str
    redirect_url: Optional[str] = None

class SSOCallbackRequest(BaseModel):
    saml_response: Optional[str] = None  # For SAML
    code: Optional[str] = None  # For OAuth
    state: Optional[str] = None

class SSOSessionResponse(BaseModel):
    session_id: str
    user_id: int
    organization_id: int
    provider_type: str
    created_at: Any
    expires_at: Any
    
    model_config = ConfigDict(from_attributes=True)

class SSOEventResponse(BaseModel):
    id: int
    event_type: str
    event_status: str
    provider_type: Optional[str]
    created_at: Any
    
    model_config = ConfigDict(from_attributes=True)

# --- Organization Management Endpoints (Admin) ---

@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Create a new organization (admin only).
    """
    org = SSOService.create_organization(
        db=db,
        name=org_data.name,
        domain=org_data.domain,
        slug=org_data.slug,
        sso_enabled=org_data.sso_enabled
    )
    return org

@router.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    List all organizations (admin only).
    """
    orgs = db.query(Organization).offset(skip).limit(limit).all()
    return orgs

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get organization details.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Only allow access to own organization or admins
    if current_user.organization_id != org_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return org

# --- SSO Configuration Endpoints (Admin) ---

@router.post("/organizations/{org_id}/sso-config", response_model=SSOConfigResponse)
def create_sso_config(
    org_id: int,
    config_data: SSOConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Create SSO configuration for an organization (admin only).
    """
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Build config dict
    config_dict = {
        "entity_id": config_data.entity_id,
        "idp_entity_id": config_data.idp_entity_id,
        "sso_url": config_data.sso_url,
        "x509_cert": config_data.x509_cert,
        "client_id": config_data.client_id,
        "client_secret": config_data.client_secret,  # TODO: Encrypt in production
        "authorization_endpoint": config_data.authorization_endpoint,
        "token_endpoint": config_data.token_endpoint,
        "userinfo_endpoint": config_data.userinfo_endpoint,
        "scopes": config_data.scopes,
        "attribute_mapping": config_data.attribute_mapping or {},
        "role_mapping": config_data.role_mapping or {},
        "jit_enabled": config_data.jit_enabled,
        "auto_assign_roles": config_data.auto_assign_roles
    }
    
    config = SSOService.create_sso_config(
        db=db,
        organization_id=org_id,
        provider_type=config_data.provider_type,
        provider_name=config_data.provider_name,
        config_data=config_dict
    )
    
    # Enable SSO on organization
    org.sso_enabled = True
    org.sso_provider = config_data.provider_name
    db.commit()
    
    return config

@router.get("/organizations/{org_id}/sso-config", response_model=SSOConfigResponse)
def get_sso_config(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get SSO configuration for an organization.
    """
    # Only allow access to own organization or admins
    if current_user.organization_id != org_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    config = SSOService.get_sso_config(db, org_id)
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    return config

@router.get("/login/{slug}")
async def initiate_sso_login(
    slug: str,
    request: Request,
    db: Session = Depends(deps.get_db)
):
    """
    Initiate SSO login flow for an organization.
    Redirects to the IdP's login page.
    """
    # Get organization
    org = SSOService.get_organization_by_slug(db, slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.sso_enabled:
        raise HTTPException(status_code=400, detail="SSO not enabled for this organization")
    
    # Get SSO config
    config = SSOService.get_sso_config(db, org.id)
    if not config:
        raise HTTPException(status_code=400, detail="SSO not configured")
    
    # Generate state/relay_state
    # For OAuth, state prevents CSRF. For SAML, RelayState preserves state.
    state = f"{slug}:{secrets.token_urlsafe(32)}"
    
    # TODO: Store state in redis/cookie to verify on callback
    
    if config.provider_type == SSOProviderType.SAML:
        if not SAML_AVAILABLE:
             raise HTTPException(status_code=501, detail="SAML support not available")
             
        req_data = prepare_flask_request(request)
        saml_service = SAMLService(config, req_data)
        
        # Return to frontend dashboard after login
        return_to = f"{settings.BASE_URL}/dashboard"
        login_url = saml_service.get_login_url(return_to=return_to)
        
        return {
            "redirect_url": login_url,
            "provider": config.provider_name,
            "type": config.provider_type
        }
        
    elif config.provider_type in [SSOProviderType.OAUTH, SSOProviderType.OIDC]:
        if not OAUTH_AVAILABLE:
            raise HTTPException(status_code=501, detail="OAuth support not available")
            
        oauth_service = OAuthService(config)
        auth_url = oauth_service.get_authorization_url(state=state)
        
        return {
            "redirect_url": auth_url,
            "provider": config.provider_name,
            "type": config.provider_type
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider type")


@router.post("/callback/saml")
async def handle_saml_callback(
    request: Request,
    db: Session = Depends(deps.get_db)
):
    """
    Handle SAML ACS (Assertion Consumer Service) callback.
    """
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")
    
    if not saml_response:
        raise HTTPException(status_code=400, detail="Missing SAMLResponse")
        
    # TODO: Implement Issuer extraction. 
    # For this implementation, we will fetch the config based on a query param 'slug' if present,
    # or fallback to a default/first config for testing.
    slug = request.query_params.get("slug")
    config = None
    
    if slug:
        org = SSOService.get_organization_by_slug(db, slug)
        if org:
            config = SSOService.get_sso_config(db, org.id)
            
    if not config:
        # Fallback: Try to find any active SAML config (NOT SAFE FOR MULTI-TENANT PRODUCTION without Issuer check)
        # In a real implementation, we MUST parse the Issuer from the XML before verification.
        config = db.query(SSOConfig).filter(SSOConfig.provider_type == SSOProviderType.SAML).first()
        
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    if not SAML_AVAILABLE:
        raise HTTPException(status_code=501, detail="SAML support not available")
    
    req_data = prepare_flask_request(request)
    # Add post_data explicitly
    req_data["post_data"] = {"SAMLResponse": saml_response}
    
    saml_service = SAMLService(config, req_data)
    success, user_attrs, error = saml_service.process_response({"SAMLResponse": saml_response})
    
    if not success:
        raise HTTPException(status_code=400, detail=f"SAML authentication failed: {error}")
        
    # JIT Provisioning
    try:
        user = SSOService.provision_user_from_sso(db, config.organization, user_attrs, config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Create Session
    session = SSOService.create_sso_session(
        db=db,
        user_id=user.id,
        organization_id=config.organization_id,
        provider_type=SSOProviderType.SAML,
        login_method="saml_acs",
        provider_session_id=user_attrs.get("session_index"),
        name_id=user_attrs.get("sso_external_id"),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Generate JWT
    from app.core.security import create_access_token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Log success
    SSOService.log_sso_event(
        db=db,
        organization_id=config.organization_id,
        event_type="login",
        event_status="success",
        provider_type="SAML",
        user_id=user.id,
        ip_address=request.client.host,
        details={"method": "saml_acs"}
    )
    
    # Redirect to frontend with token
    # In production, use a secure cookie or a redirect with a short-lived code
    redirect_url = f"{settings.BASE_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/callback/oauth")
async def handle_oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(deps.get_db)
):
    """
    Handle OAuth/OIDC callback.
    """
    # We need to know which org this is for.
    # The 'state' parameter should ideally contain the org slug or ID (encrypted/signed).
    # For now, let's assume we pass slug as a query param in the redirect URI or encoded in state.
    # Let's assume state = "slug:random_string"
    
    try:
        slug_part = state.split(":")[0]
        org_slug = slug_part
    except:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    org = SSOService.get_organization_by_slug(db, org_slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    config = SSOService.get_sso_config(db, org.id)
    if not config:
        raise HTTPException(status_code=400, detail="SSO config not found")
        
    if not OAUTH_AVAILABLE:
        raise HTTPException(status_code=501, detail="OAuth support not available")
        
    oauth_service = OAuthService(config)
    
    # Exchange code
    success, tokens, error = await oauth_service.exchange_code(code)
    if not success:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")
        
    # Get user info
    success, user_info, error = await oauth_service.get_user_info(tokens["access_token"])
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to get user info: {error}")
        
    # JIT Provisioning
    try:
        user = SSOService.provision_user_from_sso(db, org, user_info, config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Create Session
    try:
        session = SSOService.create_sso_session(
            db=db,
            user_id=user.id,
            organization_id=org.id,
            provider_type=config.provider_type,
            login_method="oauth_callback",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Generate JWT
        from app.core.security import create_access_token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        # Log success
        SSOService.log_sso_event(
            db=db,
            organization_id=org.id,
            event_type="login",
            event_status="success",
            provider_type=config.provider_type,
            user_id=user.id,
            ip_address=request.client.host
        )
        
        # Redirect to frontend
        redirect_url = f"{settings.BASE_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.post("/logout")
def sso_logout(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Logout from SSO session.
    """
    SSOService.end_sso_session(db, session_id)
    
    # Log event
    if current_user.organization_id:
        SSOService.log_sso_event(
            db=db,
            organization_id=current_user.organization_id,
            event_type="logout",
            event_status="success",
            user_id=current_user.id
        )
    
    return {"message": "Logged out successfully"}

# --- Session Management ---

@router.get("/sessions/active", response_model=List[SSOSessionResponse])
def get_active_sessions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get active SSO sessions for current user.
    """
    sessions = SSOService.get_active_sso_sessions(db, current_user.id)
    return sessions

# --- Audit Logs ---

@router.get("/organizations/{org_id}/audit-logs", response_model=List[SSOEventResponse])
def get_audit_logs(
    org_id: int,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Get SSO audit logs for an organization (admin only).
    """
    query = db.query(SSOAuditLog).filter(SSOAuditLog.organization_id == org_id)
    
    if event_type:
        query = query.filter(SSOAuditLog.event_type == event_type)
    
    logs = query.order_by(SSOAuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

# --- Test SSO Connection ---

@router.post("/organizations/{org_id}/test-connection")
async def test_sso_connection(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Test SSO connection (admin only).
    """
    config = SSOService.get_sso_config(db, org_id)
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    
    if config.provider_type == SSOProviderType.SAML:
        if not SAML_AVAILABLE:
            return {"status": "error", "message": "SAML support not installed"}
            
        try:
            # Mock request
            req_data = {
                'https': 'on',
                'http_host': 'localhost',
                'script_name': '/',
                'get_data': {},
                'post_data': {}
            }
            service = SAMLService(config, req_data)
            is_valid, expiry = service.validate_certificate()
            
            return {
                "status": "success" if is_valid else "warning",
                "message": "Configuration valid" if is_valid else "Certificate expired or invalid",
                "provider": config.provider_name,
                "cert_expiry": expiry
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration error: {str(e)}",
                "provider": config.provider_name
            }
            
    elif config.provider_type in [SSOProviderType.OAUTH, SSOProviderType.OIDC]:
        if not OAUTH_AVAILABLE:
            return {"status": "error", "message": "OAuth support not installed"}
            
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # Try to reach the authorization endpoint
                resp = await client.get(config.authorization_endpoint)
                # We expect 200 or 400 (missing params), but connectivity is what matters
                reachable = resp.status_code < 500
                
                return {
                    "status": "success" if reachable else "error",
                    "message": "Endpoint reachable" if reachable else f"Endpoint returned {resp.status_code}",
                    "provider": config.provider_name
                }
        except Exception as e:
             return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "provider": config.provider_name
            }
            
    return {"status": "unknown", "message": "Unknown provider type"}
