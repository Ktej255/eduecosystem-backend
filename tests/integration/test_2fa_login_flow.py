from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.utils import random_email, random_lower_string
from app.crud import user as crud_user
from app.schemas.user import UserCreate
import pyotp


def test_2fa_login_flow_integration(client: TestClient, db: Session):
    # 1. Create a user
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, full_name="2FA Test User")
    user = crud_user.create(db, obj_in=user_in)

    # 2. Login initially (should succeed without 2FA)
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens.get("require_2fa") is False
    auth_header = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 3. Setup 2FA
    r = client.post(f"{settings.API_V1_STR}/auth/2fa/setup", headers=auth_header)
    assert r.status_code == 200
    setup_data = r.json()
    secret = setup_data["secret"]

    # 4. Verify Setup
    totp = pyotp.TOTP(secret)
    code = totp.now()
    r = client.post(
        f"{settings.API_V1_STR}/auth/2fa/verify-setup",
        json={"code": code, "secret": secret},
        headers=auth_header,
    )
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["success"] is True
    backup_codes = response_data.get("backup_codes", [])

    # Reload user to confirm 2FA is enabled
    db.refresh(user)
    assert user.is_2fa_enabled is True

    # 5. Login again (should require 2FA)
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    response_data = r.json()
    assert response_data.get("require_2fa") is True
    temp_token = response_data["access_token"]

    # 6. Verify Login with 2FA code
    # Wait a moment or generate new code if needed, but usually same window works in tests
    # For robustness in tests, we might need to ensure time sync or just use current code
    code = totp.now()

    # Using the temp token to verify
    temp_auth_header = {"Authorization": f"Bearer {temp_token}"}
    r = client.post(
        f"{settings.API_V1_STR}/auth/2fa/verify-login",
        json={"code": code},
        headers=temp_auth_header,
    )
    assert r.status_code == 200
    final_tokens = r.json()
    assert "access_token" in final_tokens
    assert final_tokens["token_type"] == "bearer"

    # 7. Verify access with final token
    final_auth_header = {"Authorization": f"Bearer {final_tokens['access_token']}"}
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=final_auth_header)
    assert r.status_code == 200
    assert r.json()["email"] == email

    # Use backup codes from setup
    assert len(backup_codes) > 0

    # Login with backup code
    backup_code = backup_codes[0]

    # Start login flow again
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    temp_token_2 = r.json()["access_token"]

    r = client.post(
        f"{settings.API_V1_STR}/auth/2fa/verify-login",
        json={"code": backup_code},
        headers={"Authorization": f"Bearer {temp_token_2}"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
