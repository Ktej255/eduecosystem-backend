"""
SSO Authentication Service

Core service for handling SSO authentication flows (SAML, OAuth, OIDC).
Supports Azure AD, Google Workspace, and generic SAML providers.
"""

import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.sso import (
    Organization,
    SSOConfig,
    SSOSession,
    SSOAuditLog,
    SSOProviderType,
)
from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class SSOService:
    """
    Handle SSO authentication flows and user provisioning.
    """

    @staticmethod
    def create_organization(
        db: Session, name: str, domain: str, slug: str, sso_enabled: bool = False
    ) -> Organization:
        """Create a new organization."""
        org = Organization(name=name, domain=domain, slug=slug, sso_enabled=sso_enabled)
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_organization_by_domain(db: Session, domain: str) -> Optional[Organization]:
        """Get organization by email domain."""
        return db.query(Organization).filter(Organization.domain == domain).first()

    @staticmethod
    def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        return db.query(Organization).filter(Organization.slug == slug).first()

    @staticmethod
    def create_sso_config(
        db: Session,
        organization_id: int,
        provider_type: SSOProviderType,
        provider_name: str,
        config_data: Dict,
    ) -> SSOConfig:
        """
        Create SSO configuration for an organization.

        Args:
            db: Database session
            organization_id: ID of the organization
            provider_type: 'saml', 'oidc', or 'oauth'
            provider_name: Display name (e.g., 'Azure AD', 'Google Workspace')
            config_data: Provider-specific configuration
        """
        config = SSOConfig(
            organization_id=organization_id,
            provider_type=provider_type,
            provider_name=provider_name,
            **config_data,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def get_sso_config(db: Session, organization_id: int) -> Optional[SSOConfig]:
        """Get active SSO config for organization."""
        return (
            db.query(SSOConfig)
            .filter(
                SSOConfig.organization_id == organization_id,
                SSOConfig.is_active == True,
            )
            .first()
        )

    @staticmethod
    def provision_user_from_sso(
        db: Session, organization: Organization, sso_attributes: Dict, config: SSOConfig
    ) -> User:
        """
        Just-in-time user provisioning from SSO attributes.

        Args:
            db: Database session
            organization: Organization the user belongs to
            sso_attributes: User attributes from SSO provider
            config: SSO configuration with attribute mapping

        Returns:
            User object (new or existing)
        """
        # Map SSO attributes using configured mapping
        attribute_mapping = config.attribute_mapping or {}

        email = sso_attributes.get("email") or sso_attributes.get(
            attribute_mapping.get("email", "email")
        )
        first_name = sso_attributes.get("first_name") or sso_attributes.get(
            attribute_mapping.get("first_name", "given_name")
        )
        last_name = sso_attributes.get("last_name") or sso_attributes.get(
            attribute_mapping.get("last_name", "family_name")
        )
        external_id = sso_attributes.get("sub") or sso_attributes.get("name_id")

        if not email:
            raise ValueError("Email is required for SSO user provisioning")

        # Check if user already exists
        user = db.query(User).filter(User.email == email).first()

        if not user and config.jit_enabled:
            # Create new user (JIT provisioning)
            user = User(
                email=email,
                username=email.split("@")[0],  # Use email prefix as username
                full_name=f"{first_name or ''} {last_name or ''}".strip(),
                is_sso_user=True,
                organization_id=organization.id,
                sso_external_id=external_id,
                is_active=True,
                is_verified=True,  # SSO users are pre-verified
                hashed_password=get_password_hash(
                    secrets.token_urlsafe(32)
                ),  # Random password (won't be used)
            )
            db.add(user)
            logger.info(f"JIT provisioned new SSO user: {email}")
        elif user:
            # Update existing user
            if not user.organization_id:
                user.organization_id = organization.id
            user.is_sso_user = True
            user.sso_external_id = external_id
            logger.info(f"Updated existing user for SSO: {email}")
        else:
            raise ValueError("JIT provisioning is disabled and user does not exist")

        # Map roles from SSO groups (if configured)
        if config.auto_assign_roles and "groups" in sso_attributes:
            SSOService._assign_roles_from_groups(
                user, sso_attributes["groups"], config.role_mapping
            )

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def _assign_roles_from_groups(user: User, groups: list, role_mapping: Dict):
        """
        Assign roles to user based on SSO group membership.

        Args:
            user: User object
            groups: List of group names/IDs from SSO
            role_mapping: Mapping of group names to roles
        """
        for group in groups:
            role = role_mapping.get(group)
            if role:
                user.role = role  # Simple role assignment (could be enhanced with RBAC)
                logger.info(
                    f"Assigned role '{role}' to user {user.email} from group '{group}'"
                )
                break  # Take first matching role

    @staticmethod
    def create_sso_session(
        db: Session,
        user_id: int,
        organization_id: int,
        provider_type: SSOProviderType,
        login_method: str,
        provider_session_id: Optional[str] = None,
        name_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_timeout_hours: int = 8,
    ) -> SSOSession:
        """
        Create SSO session for tracking and logout.

        Args:
            db: Database session
            user_id: User ID
            organization_id: Organization ID
            provider_type: SSO provider type
            login_method: Login method identifier
            provider_session_id: Session ID from SSO provider (for SLO)
            name_id: SAML NameID (for logout)
            ip_address: User's IP address
            user_agent: User's browser user agent
            session_timeout_hours: Session timeout in hours

        Returns:
            SSOSession object
        """
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=session_timeout_hours)

        sso_session = SSOSession(
            user_id=user_id,
            organization_id=organization_id,
            session_id=session_id,
            provider_session_id=provider_session_id,
            name_id=name_id,
            provider_type=provider_type,
            login_method=login_method,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        db.add(sso_session)
        db.commit()
        db.refresh(sso_session)
        return sso_session

    @staticmethod
    def log_sso_event(
        db: Session,
        organization_id: int,
        event_type: str,
        event_status: str,
        provider_type: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        """
        Log SSO event for audit trail.

        Args:
            db: Database session
            organization_id: Organization ID
            event_type: Type of event ('login', 'logout', 'config_change', etc.)
            event_status: 'success', 'failure', 'error'
            provider_type: SSO provider type
            user_id: User ID (if applicable)
            ip_address: IP address
            user_agent: User agent
            details: Additional event details
            error_message: Error message (if failed)
        """
        log_entry = SSOAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            event_status=event_status,
            provider_type=provider_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            error_message=error_message,
        )
        db.add(log_entry)
        db.commit()

    @staticmethod
    def end_sso_session(db: Session, session_id: str):
        """Mark SSO session as logged out."""
        session = (
            db.query(SSOSession).filter(SSOSession.session_id == session_id).first()
        )
        if session:
            session.logged_out_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def get_active_sso_sessions(db: Session, user_id: int) -> list:
        """Get all active SSO sessions for a user."""
        now = datetime.utcnow()
        return (
            db.query(SSOSession)
            .filter(
                SSOSession.user_id == user_id,
                SSOSession.logged_out_at.is_(None),
                SSOSession.expires_at > now,
            )
            .all()
        )


class SAMLService:
    """
    SAML 2.0 authentication service using python3-saml.
    """

    @staticmethod
    def _get_saml_settings(config: SSOConfig) -> dict:
        """
        Convert database config to python3-saml settings dict.
        """
        return {
            "strict": True,
            "debug": True,  # TODO: Disable in production
            "sp": {
                "entityId": config.entity_id or "https://app.eduecosystem.com",
                "assertionConsumerService": {
                    "url": "https://app.eduecosystem.com/api/v1/sso/callback/saml",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": "https://app.eduecosystem.com/api/v1/sso/logout",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
                "x509cert": "",  # TODO: Load SP cert from file/env
                "privateKey": "",  # TODO: Load SP key from file/env
            },
            "idp": {
                "entityId": config.idp_entity_id,
                "singleSignOnService": {
                    "url": config.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": config.slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": config.x509_cert,
            },
        }

    @staticmethod
    def build_auth_request(
        config: SSOConfig, relay_state: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Build SAML authentication request.

        Returns:
            (auth_url, request_id)
        """
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
            from onelogin.saml2.utils import OneLogin_Saml2_Utils
        except ImportError:
            logger.error("python3-saml not installed")
            raise Exception("SAML support not available")

        # Mock request object required by python3-saml
        req = {
            "https": "on",
            "http_host": "app.eduecosystem.com",
            "script_name": "/api/v1/sso/login",
            "server_port": 443,
            "get_data": {},
            "post_data": {},
        }

        settings = SAMLService._get_saml_settings(config)
        auth = OneLogin_Saml2_Auth(req, settings)

        # return_to (RelayState)
        return_to = relay_state or "/"

        return auth.login(return_to=return_to), auth.get_last_request_id()

    @staticmethod
    def process_saml_response(saml_response: str, config: SSOConfig) -> Dict:
        """
        Process and validate SAML response.

        Returns:
            User attributes from SAML assertion
        """
        try:
            from onelogin.saml2.auth import OneLogin_Saml2_Auth
        except ImportError:
            raise Exception("SAML support not available")

        req = {
            "https": "on",
            "http_host": "app.eduecosystem.com",
            "script_name": "/api/v1/sso/callback/saml",
            "server_port": 443,
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response},
        }

        settings = SAMLService._get_saml_settings(config)
        auth = OneLogin_Saml2_Auth(req, settings)

        auth.process_response()

        errors = auth.get_errors()
        if errors:
            logger.error(f"SAML processing errors: {errors}")
            raise Exception(
                f"SAML authentication failed: {auth.get_last_error_reason()}"
            )

        if not auth.is_authenticated():
            raise Exception("SAML authentication failed: Not authenticated")

        return {
            "attributes": auth.get_attributes(),
            "name_id": auth.get_nameid(),
            "session_index": auth.get_session_index(),
        }


class OAuthService:
    """
    OAuth 2.0 / OIDC authentication service using authlib.
    """

    @staticmethod
    def _get_oauth_client(config: SSOConfig):
        try:
            from authlib.integrations.requests_client import OAuth2Session
        except ImportError:
            logger.error("authlib not installed")
            raise Exception("OAuth support not available")

        return OAuth2Session(
            client_id=config.client_id,
            client_secret=config.client_secret,
            scope=" ".join(config.scopes or ["openid", "email", "profile"]),
            redirect_uri="https://app.eduecosystem.com/api/v1/sso/callback/oauth",
        )

    @staticmethod
    def build_authorization_url(
        config: SSOConfig, redirect_uri: str, state: str
    ) -> str:
        """
        Build OAuth authorization URL.
        """
        client = OAuthService._get_oauth_client(config)
        uri, _ = client.create_authorization_url(
            config.authorization_endpoint, state=state
        )
        return uri

    @staticmethod
    def exchange_code_for_token(
        code: str, config: SSOConfig, redirect_uri: str
    ) -> Dict:
        """
        Exchange authorization code for access token and ID token.
        """
        client = OAuthService._get_oauth_client(config)
        token = client.fetch_token(
            config.token_endpoint, code=code, grant_type="authorization_code"
        )
        return token

    @staticmethod
    def get_user_info(access_token: str, config: SSOConfig) -> Dict:
        """
        Get user information from OAuth userinfo endpoint.
        """
        import requests

        response = requests.get(
            config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
