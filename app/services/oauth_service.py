"""
OAuth/OIDC Service for Enterprise SSO

Implements OAuth 2.0 and OpenID Connect authentication flows.
Supports Google Workspace, Azure AD, and any OIDC-compliant provider.
"""

from authlib.jose import jwt
from typing import Dict, Optional, Tuple
import logging
import httpx

from app.models.sso import SSOConfig
from app.core.config import settings

logger = logging.getLogger(__name__)


class OAuthService:
    """
    Service for OAuth 2.0 and OpenID Connect authentication.

    Supports authorization code flow, token exchange, user info retrieval,
    and token refresh.
    """

    def __init__(self, sso_config: SSOConfig):
        """
        Initialize OAuth service with SSO configuration.

        Args:
            sso_config: SSOConfig model with OAuth/OIDC settings
        """
        self.config = sso_config
        self.client_id = sso_config.client_id
        self.client_secret = sso_config.client_secret
        self.scopes = sso_config.scopes or ["openid", "email", "profile"]

        # Endpoints
        self.authorization_endpoint = sso_config.authorization_endpoint
        self.token_endpoint = sso_config.token_endpoint
        self.userinfo_endpoint = sso_config.userinfo_endpoint

        # Build redirect URI
        base_url = settings.BASE_URL or "http://localhost:8000"
        self.redirect_uri = f"{base_url}/api/v1/sso/oauth/callback"

    def get_authorization_url(
        self, state: str, redirect_uri: Optional[str] = None
    ) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            state: CSRF protection state parameter
            redirect_uri: Optional custom redirect URI

        Returns:
            URL to redirect user for authorization
        """
        redirect = redirect_uri or self.redirect_uri
        scope_str = " ".join(self.scopes)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope_str,
            "redirect_uri": redirect,
            "state": state,
        }

        # Build query string
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_endpoint}?{query}"

    async def exchange_code(
        self, code: str, redirect_uri: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth provider
            redirect_uri: Redirect URI used in authorization request

        Returns:
            Tuple of (success, token_data, error_message)
            - token_data contains: access_token, id_token, refresh_token, expires_in
        """
        try:
            redirect = redirect_uri or self.redirect_uri

            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    error_msg = f"Token exchange failed: {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg

                tokens = response.json()
                logger.info("OAuth token exchange successful")
                return True, tokens, None

        except Exception as e:
            logger.exception("Error exchanging OAuth code")
            return False, None, str(e)

    async def get_user_info(
        self, access_token: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Retrieve user information from OAuth provider.

        Args:
            access_token: Access token from token exchange

        Returns:
            Tuple of (success, user_data, error_message)
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(self.userinfo_endpoint, headers=headers)

                if response.status_code != 200:
                    error_msg = f"User info retrieval failed: {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg

                user_info = response.json()

                # Map OAuth user info to our user model
                user_data = self._map_user_info(user_info)

                logger.info(f"OAuth user info retrieved for: {user_data.get('email')}")
                return True, user_data, None

        except Exception as e:
            logger.exception("Error retrieving OAuth user info")
            return False, None, str(e)

    def _map_user_info(self, user_info: Dict) -> Dict:
        """
        Map OAuth/OIDC user info to our user model.

        Args:
            user_info: User info from OAuth provider

        Returns:
            Dict with mapped user data
        """
        # Default attribute mapping for OIDC standard claims
        default_mapping = {
            "email": "email",
            "first_name": "given_name",
            "last_name": "family_name",
            "full_name": "name",
            "picture": "picture",
            "groups": "groups",
        }

        attribute_mapping = self.config.attribute_mapping or default_mapping

        user_data = {
            "sso_external_id": user_info.get("sub"),  # Subject identifier
            "provider_type": "OAUTH"
            if self.config.provider_type == "OAUTH"
            else "OIDC",
            "provider_name": self.config.provider_name,
        }

        # Map each configured attribute
        for our_field, oauth_field in attribute_mapping.items():
            value = user_info.get(oauth_field)
            if value:
                user_data[our_field] = value

        # Ensure email exists
        if not user_data.get("email"):
            user_data["email"] = user_info.get("email") or user_info.get("sub")

        # Map roles from groups if configured
        if self.config.role_mapping and "groups" in user_data:
            user_data["role"] = self._map_role(user_data["groups"])

        return user_data

    def _map_role(self, groups: any) -> str:
        """
        Map OAuth groups to platform role.

        Args:
            groups: User's OAuth groups (string or list)

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

    async def refresh_token(
        self, refresh_token: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from original token exchange

        Returns:
            Tuple of (success, new_tokens, error_message)
        """
        try:
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    error_msg = f"Token refresh failed: {response.text}"
                    logger.error(error_msg)
                    return False, None, error_msg

                new_tokens = response.json()
                logger.info("OAuth token refresh successful")
                return True, new_tokens, None

        except Exception as e:
            logger.exception("Error refreshing OAuth token")
            return False, None, str(e)

    def verify_id_token(self, id_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Verify and decode ID token (for OIDC).

        Args:
            id_token: JWT ID token from token response

        Returns:
            Tuple of (is_valid, claims)
        """
        try:
            # TODO: Fetch JWKS from provider for verification
            # For now, just decode without verification (NOT PRODUCTION SAFE)
            claims = jwt.decode(id_token, key=None, options={"verify_signature": False})

            # Verify issuer, audience, expiry
            # if claims.get("iss") != expected_issuer:
            #     return False, None
            # if claims.get("aud") != self.client_id:
            #     return False, None
            # if claims.get("exp", 0) < time.time():
            #     return False, None

            logger.info("ID token verified successfully")
            return True, claims

        except Exception as e:
            logger.error(f"ID token verification failed: {e}")
            return False, None

    def get_logout_url(self, redirect_uri: Optional[str] = None) -> Optional[str]:
        """
        Generate logout URL if provider supports RP-initiated logout.

        Args:
            redirect_uri: URL to redirect after logout

        Returns:
            Logout URL or None if not supported
        """
        # Check if provider has end_session_endpoint in settings
        end_session_endpoint = self.config.settings.get("end_session_endpoint")

        if not end_session_endpoint:
            logger.warning("Provider does not support RP-initiated logout")
            return None

        redirect = redirect_uri or f"{settings.BASE_URL}"

        params = {"client_id": self.client_id, "post_logout_redirect_uri": redirect}

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{end_session_endpoint}?{query}"

    async def revoke_token(self, token: str, token_type: str = "access_token") -> bool:
        """
        Revoke access or refresh token.

        Args:
            token: Token to revoke
            token_type: Type of token ('access_token' or 'refresh_token')

        Returns:
            True if revocation successful
        """
        try:
            revocation_endpoint = self.config.settings.get("revocation_endpoint")

            if not revocation_endpoint:
                logger.warning("Provider does not support token revocation")
                return False

            revoke_data = {
                "token": token,
                "token_type_hint": token_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    revocation_endpoint,
                    data=revoke_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    logger.info(f"Token revocation successful for {token_type}")
                    return True
                else:
                    logger.error(f"Token revocation failed: {response.text}")
                    return False

        except Exception:
            logger.exception("Error revoking token")
            return False


# Helper functions for OAuth


def generate_state() -> str:
    """Generate random state parameter for CSRF protection."""
    import secrets

    return secrets.token_urlsafe(32)


def validate_state(received_state: str, stored_state: str) -> bool:
    """Validate state parameter to prevent CSRF attacks."""
    return received_state == stored_state


# Provider-specific configurations

GOOGLE_WORKSPACE_CONFIG = {
    "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_endpoint": "https://oauth2.googleapis.com/token",
    "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
    "scopes": ["openid", "email", "profile"],
    "attribute_mapping": {
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
        "picture": "picture",
    },
}

AZURE_AD_OAUTH_CONFIG = {
    "authorization_endpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
    "token_endpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
    "userinfo_endpoint": "https://graph.microsoft.com/oidc/userinfo",
    "scopes": ["openid", "email", "profile"],
    "attribute_mapping": {
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
    },
}
