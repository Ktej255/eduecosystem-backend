"""
SAML Service for Enterprise SSO

Implements SAML 2.0 authentication flow for enterprise single sign-on.
Handles SAML login, assertion processing, logout, and metadata generation.
"""

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

from app.models.sso import SSOConfig
from app.core.config import settings

logger = logging.getLogger(__name__)


class SAMLService:
    """
    Service for SAML 2.0 authentication.

    Supports SP-initiated and IdP-initiated flows, SLO (Single Logout),
    and attribute/role mapping.
    """

    def __init__(self, sso_config: SSOConfig, request_data: Optional[Dict] = None):
        """
        Initialize SAML service with SSO configuration.

        Args:
            sso_config: SSOConfig model with SAML settings
            request_data: Optional HTTP request data (URL, query params)
        """
        self.config = sso_config
        self.request_data = request_data or {}
        self.saml_settings = self._build_saml_settings()

    def _build_saml_settings(self) -> Dict:
        """
        Build SAML settings dict from SSOConfig.

        Returns:
            Dictionary compatible with OneLogin_Saml2_Settings
        """
        # Base URL for this service provider
        base_url = settings.BASE_URL or "http://localhost:8000"
        acs_url = f"{base_url}/api/v1/sso/saml/acs"
        sls_url = f"{base_url}/api/v1/sso/saml/sls"

        saml_settings = {
            "strict": True,
            "debug": settings.DEBUG,
            "sp": {
                "entityId": self.config.entity_id or f"{base_url}/saml/metadata",
                "assertionConsumerService": {
                    "url": acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": sls_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "x509cert": "",  # SP certificate (optional for encryption)
                "privateKey": "",  # SP private key (optional for encryption)
            },
            "idp": {
                "entityId": self.config.idp_entity_id,
                "singleSignOnService": {
                    "url": self.config.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": self.config.slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.config.x509_cert,
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": False,
                "logoutRequestSigned": False,
                "logoutResponseSigned": False,
                "signMetadata": False,
                "wantMessagesSigned": False,
                "wantAssertionsSigned": True,
                "wantNameIdEncrypted": False,
                "requestedAuthnContext": True,
                "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
            },
        }

        return saml_settings

    def get_login_url(self, return_to: Optional[str] = None) -> str:
        """
        Generate SAML login URL for SP-initiated flow.

        Args:
            return_to: URL to redirect after successful authentication

        Returns:
            URL to redirect user to IdP for authentication
        """
        auth = OneLogin_Saml2_Auth(self.request_data, self.saml_settings)
        return auth.login(return_to=return_to)

    def process_response(
        self, post_data: Dict
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Process SAML response from IdP.

        Args:
            post_data: POST data containing SAMLResponse

        Returns:
            Tuple of (success, user_data, error_message)
            - success: True if authentication successful
            - user_data: Dict with user attributes if successful
            - error_message: Error description if failed
        """
        try:
            # Update request data with POST params
            request_data = {**self.request_data, "post_data": post_data}

            auth = OneLogin_Saml2_Auth(request_data, self.saml_settings)
            auth.process_response()

            errors = auth.get_errors()
            if errors:
                error_reason = auth.get_last_error_reason()
                logger.error(f"SAML authentication failed: {error_reason}")
                return False, None, error_reason

            if not auth.is_authenticated():
                logger.warning("SAML response processed but user not authenticated")
                return False, None, "Authentication failed"

            # Extract user attributes
            attributes = auth.get_attributes()
            name_id = auth.get_nameid()
            session_index = auth.get_session_index()

            # Map SAML attributes to our user model
            user_data = self._map_attributes(attributes, name_id, session_index)

            logger.info(f"SAML authentication successful for: {user_data.get('email')}")
            return True, user_data, None

        except Exception as e:
            logger.exception("Error processing SAML response")
            return False, None, str(e)

    def _map_attributes(
        self, attributes: Dict, name_id: str, session_index: Optional[str]
    ) -> Dict:
        """
        Map SAML attributes to user data using attribute_mapping config.

        Args:
            attributes: SAML attributes from IdP
            name_id: SAML NameID (usually email)
            session_index: SAML session index for logout

        Returns:
            Dict with mapped user data
        """
        # Default attribute mapping if not configured
        default_mapping = {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
            "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
            "groups": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups",
        }

        attribute_mapping = self.config.attribute_mapping or default_mapping

        user_data = {
            "sso_external_id": name_id,
            "session_index": session_index,
            "provider_type": "SAML",
            "provider_name": self.config.provider_name,
        }

        # Map each configured attribute
        for our_field, saml_field in attribute_mapping.items():
            value = attributes.get(saml_field, [None])[0]  # SAML attrs are lists
            if value:
                user_data[our_field] = value

        # Ensure email exists (fallback to NameID)
        if not user_data.get("email"):
            user_data["email"] = name_id

        # Map roles from groups if configured
        if self.config.role_mapping and "groups" in user_data:
            user_data["role"] = self._map_role(user_data["groups"])

        return user_data

    def _map_role(self, groups: any) -> str:
        """
        Map SAML groups to platform role using role_mapping config.

        Args:
            groups: User's SAML groups (string or list)

        Returns:
            Mapped role (defaults to 'student')
        """
        if not self.config.role_mapping:
            return "student"

        # Handle both string and list of groups
        user_groups = [groups] if isinstance(groups, str) else (groups or [])

        # Check each group against role mapping
        for group in user_groups:
            if group in self.config.role_mapping:
                return self.config.role_mapping[group]

        # Default role
        return "student"

    def get_logout_url(
        self,
        name_id: str,
        session_index: Optional[str] = None,
        return_to: Optional[str] = None,
    ) -> str:
        """
        Generate SAML logout URL for Single Logout (SLO).

        Args:
            name_id: User's SAML NameID
            session_index: SAML session index from login
            return_to: URL to redirect after logout

        Returns:
            URL to redirect user to IdP for logout
        """
        auth = OneLogin_Saml2_Auth(self.request_data, self.saml_settings)
        return auth.logout(
            name_id=name_id, session_index=session_index, return_to=return_to
        )

    def process_slo_response(self, get_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Process logout response from IdP.

        Args:
            get_data: GET parameters containing SAMLResponse

        Returns:
            Tuple of (success, error_message)
        """
        try:
            request_data = {**self.request_data, "get_data": get_data}

            auth = OneLogin_Saml2_Auth(request_data, self.saml_settings)
            auth.process_slo()

            errors = auth.get_errors()
            if errors:
                error_reason = auth.get_last_error_reason()
                logger.error(f"SAML logout failed: {error_reason}")
                return False, error_reason

            logger.info("SAML logout successful")
            return True, None

        except Exception as e:
            logger.exception("Error processing SAML logout response")
            return False, str(e)

    def get_metadata(self) -> str:
        """
        Generate SP metadata XML.

        Returns:
            SAML metadata XML string
        """
        settings_obj = OneLogin_Saml2_Settings(self.saml_settings)
        metadata = settings_obj.get_sp_metadata()

        errors = settings_obj.validate_metadata(metadata)
        if errors:
            logger.error(f"Invalid SP metadata: {errors}")
            raise ValueError(f"Invalid metadata: {errors}")

        return metadata

    def validate_certificate(self) -> Tuple[bool, Optional[datetime]]:
        """
        Validate IdP certificate and check expiration.

        Returns:
            Tuple of (is_valid, expiry_date)
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            import base64

            # Parse certificate
            cert_text = self.config.x509_cert
            cert_bytes = base64.b64decode(cert_text)
            cert = x509.load_der_x509_certificate(cert_bytes, default_backend())

            # Check expiration
            expiry = cert.not_valid_after
            now = datetime.utcnow()

            is_valid = now < expiry

            if not is_valid:
                logger.warning(f"IdP certificate expired on {expiry}")

            return is_valid, expiry

        except Exception as e:
            logger.error(f"Error validating certificate: {e}")
            return False, None


# Utility functions for SAML


def prepare_flask_request(request) -> Dict:
    """
    Convert FastAPI request to format expected by python3-saml.

    Args:
        request: FastAPI Request object

    Returns:
        Dict with SAML request data
    """
    return {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": {},  # Will be populated from request body
    }
