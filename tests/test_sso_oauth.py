import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.sso import Organization, SSOConfig, SSOProviderType

client = TestClient(app)


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def mock_oauth_service(mocker):
    mock = mocker.patch("app.api.api_v1.endpoints.sso.OAuthService")
    instance = mock.return_value
    instance.get_authorization_url.return_value = "https://provider.com/auth"
    instance.exchange_code = AsyncMock(
        return_value={
            "access_token": "mock_access_token",
            "id_token": "mock_id_token",
            "expires_in": 3600,
        }
    )
    instance.get_user_info = AsyncMock(
        return_value=(
            True,
            {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "sub": "12345",
            },
            None,
        )
    )
    return instance


def test_oauth_login_flow(db_session, mock_oauth_service):
    # 1. Setup Organization and Config
    org = Organization(
        id=1, name="Test Org", slug="test-org", domain="example.com", sso_enabled=True
    )

    config = SSOConfig(
        organization_id=1,
        provider_type=SSOProviderType.OAUTH,
        provider_name="Test Provider",
        client_id="client_id",
        client_secret="client_secret",
        authorization_endpoint="https://auth",
        token_endpoint="https://token",
        userinfo_endpoint="https://userinfo",
        is_active=True,
    )

    # Mock DB queries
    with patch(
        "app.services.sso_service.SSOService.get_organization_by_slug", return_value=org
    ):
        with patch(
            "app.services.sso_service.SSOService.get_sso_config", return_value=config
        ):
            # 2. Test Login Initiation
            response = client.get(
                "/api/v1/sso/login/test-org"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["redirect_url"] == "https://provider.com/auth"
            # assert "state" in data
            # state = data["state"]
            # assert state.startswith("1:")  # org_id:random

            # Extract state from redirect_url if needed for next step
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(data["redirect_url"])
            state = parse_qs(parsed_url.query)["state"][0]

            # 3. Test Callback
            # Mock DB for callback
            with patch(
                "app.services.sso_service.SSOService.get_sso_config",
                return_value=config,
            ):
                with patch(
                    "app.api.api_v1.endpoints.sso.Organization", return_value=org
                ):  # For query
                    with patch("sqlalchemy.orm.Session.query") as mock_query:
                        mock_query.return_value.filter.return_value.first.return_value = org

                        # Mock user provisioning
                        with patch(
                            "app.services.sso_service.SSOService.provision_user_from_sso"
                        ) as mock_provision:
                            mock_provision.return_value.id = 123
                            mock_provision.return_value.email = "test@example.com"
                            mock_provision.return_value.full_name = "Test User"
                            mock_provision.return_value.role = "student"

                            # Mock session creation
                            with patch(
                                "app.services.sso_service.SSOService.create_sso_session"
                            ):
                                with patch(
                                    "app.services.sso_service.SSOService.log_sso_event"
                                ):
                                    callback_response = client.post(
                                        "/api/v1/sso/callback/oauth",
                                        json={"code": "mock_code", "state": state},
                                    )

                                    assert callback_response.status_code == 200
                                    cb_data = callback_response.json()
                                    assert "access_token" in cb_data
                                    assert (
                                        cb_data["user"]["email"] == "test@example.com"
                                    )


if __name__ == "__main__":
    # Manually run if executed as script
    pass
