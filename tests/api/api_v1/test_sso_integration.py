from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from app.core.config import settings
from app.tests.utils.user import user_authentication_headers
from app.crud import user as crud_user
from app.schemas.user import UserCreate


# Helper to get superuser headers
def get_superuser_headers(client: TestClient, db: Session) -> dict:
    print("Getting superuser headers...")
    email = settings.FIRST_SUPERUSER
    password = settings.FIRST_SUPERUSER_PASSWORD
    user = crud_user.get_by_email(db, email=email)
    if not user:
        print("Creating superuser...")
        user_in = UserCreate(
            email=email, password=password, full_name="Super User", is_superuser=True
        )
        user = crud_user.create(db, obj_in=user_in)

    print("Logging in superuser...")
    return user_authentication_headers(client=client, email=email, password=password)


def test_sso_full_flow(client: TestClient, db: Session):
    """
    Test the full lifecycle of Enterprise SSO:
    1. Admin creates Organization
    2. Admin configures SSO (OAuth)
    3. User initiates Login
    4. User completes Callback
    """
    print("Starting test_sso_full_flow")

    # 1. Admin Login & Create Organization
    superuser_headers = get_superuser_headers(client, db)
    print("Got superuser headers")

    org_data = {
        "name": "Integration Test Org",
        "slug": "integration-test",
        "domain": "integration.test",
        "sso_enabled": True,
    }

    response = client.post(
        f"{settings.API_V1_STR}/sso/organizations",
        headers=superuser_headers,
        json=org_data,
    )
    assert response.status_code == 200
    org = response.json()
    org_id = org["id"]
    assert org["slug"] == "integration-test"

    # 2. Configure SSO (OAuth)
    sso_config_data = {
        "provider_type": "oauth",
        "provider_name": "Test OAuth",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "authorization_endpoint": "https://auth.example.com/authorize",
        "token_endpoint": "https://auth.example.com/token",
        "userinfo_endpoint": "https://auth.example.com/userinfo",
        "scopes": ["openid", "email", "profile"],
        "jit_enabled": True,
    }

    response = client.post(
        f"{settings.API_V1_STR}/sso/organizations/{org_id}/sso-config",
        headers=superuser_headers,
        json=sso_config_data,
    )
    assert response.status_code == 200
    config = response.json()
    assert config["provider_type"] == "oauth"

    # 3. User Initiates Login
    # This endpoint is public
    response = client.get(f"{settings.API_V1_STR}/sso/login/integration-test")
    assert response.status_code == 200
    data = response.json()
    assert "redirect_url" in data
    assert "https://auth.example.com/authorize" in data["redirect_url"]
    assert "client_id=test-client-id" in data["redirect_url"]

    # Extract state from redirect URL for callback
    import urllib.parse

    parsed = urllib.parse.urlparse(data["redirect_url"])
    params = urllib.parse.parse_qs(parsed.query)
    state = params["state"][0]

    # 4. OAuth Callback
    # We need to mock the OAuthService methods since they make external calls

    with patch(
        "app.services.oauth_service.OAuthService.exchange_code"
    ) as mock_exchange:
        with patch(
            "app.services.oauth_service.OAuthService.get_user_info"
        ) as mock_user_info:
            # Mock Token Exchange
            mock_exchange.return_value = (
                True,
                {
                    "access_token": "mock_access_token",
                    "id_token": "mock_id_token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
                None,
            )

            # Mock User Info
            mock_user_info.return_value = (
                True,
                {
                    "sub": "1234567890",
                    "name": "SSO User",
                    "first_name": "SSO",
                    "last_name": "User",
                    "email": "user@integration.test",
                    "email_verified": True,
                },
                None,
            )

            callback_response = client.get(
                f"{settings.API_V1_STR}/sso/callback/oauth",
                params={"code": "mock_auth_code", "state": state},
                follow_redirects=False,
            )

            # Expect redirect to frontend
            assert callback_response.status_code == 303
            redirect_url = callback_response.headers["location"]
            assert "token=" in redirect_url

            # Extract token
            parsed_url = urlparse(redirect_url)
            token = parse_qs(parsed_url.query)["token"][0]
            assert token

            # Verify user was created (JIT)
            user = crud_user.get_by_email(db, email="user@integration.test")
            assert user is not None
            assert user.full_name == "SSO User"
            assert user.organization_id == org_id
            assert user.is_sso_user is True


def test_sso_saml_flow(client: TestClient, db: Session):
    """
    Test SAML specific flows with mocks
    """
    # Setup Org and Config
    superuser_headers = get_superuser_headers(client, db)
    org_data = {
        "name": "SAML Org",
        "slug": "saml-test",
        "domain": "saml.test",
        "sso_enabled": True,
    }
    org_res = client.post(
        f"{settings.API_V1_STR}/sso/organizations",
        headers=superuser_headers,
        json=org_data,
    )
    org_id = org_res.json()["id"]

    saml_config = {
        "provider_type": "saml",
        "provider_name": "Test SAML",
        "entity_id": "https://idp.example.com",
        "sso_url": "https://idp.example.com/sso",
        "x509_cert": "MIID...",
        "jit_enabled": True,
    }
    client.post(
        f"{settings.API_V1_STR}/sso/organizations/{org_id}/sso-config",
        headers=superuser_headers,
        json=saml_config,
    )

    # Test Login Redirect
    # Mock SAML AuthNRequest generation
    with patch("app.api.api_v1.endpoints.sso.SAMLService.get_login_url") as mock_url:
        mock_url.return_value = "https://idp.example.com/sso?SAMLRequest=..."

        response = client.get(f"{settings.API_V1_STR}/sso/login/saml-test")
        assert response.status_code == 200
        assert (
            response.json()["redirect_url"]
            == "https://idp.example.com/sso?SAMLRequest=..."
        )

    # Test SAML Callback
    # Mock SAML Response processing
    with patch(
        "app.api.api_v1.endpoints.sso.SAMLService.process_response"
    ) as mock_process:
        mock_process.return_value = (
            True,
            {
                "email": "saml@saml.test",
                "name_id": "saml_name_id_456",
                "first_name": "SAML",
                "last_name": "User",
                "session_index": "session_123",
            },
            None,
        )

        # We need to post form data for SAML
        callback_response = client.post(
            f"{settings.API_V1_STR}/sso/callback/saml",
            data={"SAMLResponse": "mock_base64_response", "RelayState": str(org_id)},
            follow_redirects=False,
        )

        # Expect redirect
        assert callback_response.status_code == 303
        redirect_url = callback_response.headers["location"]
        assert "token=" in redirect_url

        # Verify user JIT
        user = crud_user.get_by_email(db, email="saml@saml.test")
        assert user is not None
        assert user.organization_id == org_id
        assert user.full_name == "SAML User"
