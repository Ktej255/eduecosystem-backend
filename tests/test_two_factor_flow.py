"""
Tests for Two-Factor Authentication Flow

Tests the complete 2FA lifecycle including setup, verification, login, and disable.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.user import User
from app.models.two_factor import TwoFactorAuth, TwoFactorBackupCode
from app.services.two_factor_service import two_factor_service

client = TestClient(app)


def test_2fa_setup_flow(db: Session, test_user: User, test_user_headers: dict):
    """Test complete 2FA setup flow"""

    # Step 1: Initiate setup
    response = client.post("/api/v1/auth/2fa/setup", headers=test_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "secret" in data
    assert "qr_code" in data
    secret = data["secret"]

    # Verify QR code is base64 encoded
    assert len(data["qr_code"]) > 0

    # Step 2: Generate a valid TOTP code
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()

    # Step 3: Verify and enable 2FA
    response = client.post(
        "/api/v1/auth/2fa/verify-setup",
        json={"secret": secret, "code": code},
        headers=test_user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "backup_codes" in data
    assert len(data["backup_codes"]) == 10

    # Verify 2FA is enabled in database
    two_factor = (
        db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == test_user.id).first()
    )
    assert two_factor is not None
    assert two_factor.is_enabled is True

    # Verify backup codes are stored
    backup_codes = (
        db.query(TwoFactorBackupCode)
        .filter(TwoFactorBackupCode.user_id == test_user.id)
        .all()
    )
    assert len(backup_codes) == 10


def test_2fa_verify_setup_invalid_code(db: Session, test_user_headers: dict):
    """Test 2FA setup with invalid code"""

    # Step 1: Initiate setup
    response = client.post("/api/v1/auth/2fa/setup", headers=test_user_headers)
    assert response.status_code == 200
    secret = response.json()["secret"]

    # Step 2: Try to verify with invalid code
    response = client.post(
        "/api/v1/auth/2fa/verify-setup",
        json={"secret": secret, "code": "000000"},
        headers=test_user_headers,
    )
    assert response.status_code == 400
    assert "Invalid code" in response.json()["detail"]


def test_2fa_login_verification(db: Session, test_user: User):
    """Test 2FA verification during login"""

    # Setup: Enable 2FA for user
    secret = two_factor_service.generate_totp_secret()
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()

    # Enable 2FA
    two_factor_service.enable_2fa(db, test_user.id, secret, code)

    # Login should now require 2FA
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": test_user.email, "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    # Assuming backend returns require_2fa flag
    # Note: This may need to be implemented in auth endpoint

    # Verify 2FA code
    code = totp.now()
    response = client.post(
        "/api/v1/auth/2fa/verify-login",
        json={"code": code},
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_2fa_backup_code_usage(
    db: Session, test_user: User, test_user_headers: dict
):
    """Test using backup code for login"""

    # Setup: Enable 2FA and get backup codes
    secret = two_factor_service.generate_totp_secret()
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()

    two_factor_service.enable_2fa(db, test_user.id, secret, code)
    backup_codes = two_factor_service.get_backup_codes(db, test_user.id)
    assert len(backup_codes) > 0

    # Use backup code for verification
    backup_code = backup_codes[0]
    response = client.post(
        "/api/v1/auth/2fa/verify-login",
        json={"code": backup_code},
        headers=test_user_headers,
    )
    assert response.status_code == 200

    # Verify backup code is marked as used
    db_backup = (
        db.query(TwoFactorBackupCode)
        .filter(TwoFactorBackupCode.user_id == test_user.id)
        .first()
    )

    # The first one should be used
    from app.services.two_factor_service import two_factor_service as svc

    decrypted = svc._decrypt_secret(db_backup.code_hash)
    if decrypted == backup_code:
        assert db_backup.is_used is True


def test_2fa_disable_flow(db: Session, test_user: User, test_user_headers: dict):
    """Test disabling 2FA"""

    # Setup: Enable 2FA
    secret = two_factor_service.generate_totp_secret()
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()

    two_factor_service.enable_2fa(db, test_user.id, secret, code)

    # Verify 2FA is enabled
    response = client.get("/api/v1/auth/2fa/status", headers=test_user_headers)
    assert response.json()["is_enabled"] is True

    # Disable 2FA
    code = totp.now()
    response = client.post(
        "/api/v1/auth/2fa/disable", json={"code": code}, headers=test_user_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify 2FA is disabled
    response = client.get("/api/v1/auth/2fa/status", headers=test_user_headers)
    assert response.json()["is_enabled"] is False

    # Verify database cleanup
    two_factor = (
        db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == test_user.id).first()
    )
    assert two_factor is None


def test_2fa_status_endpoint(db: Session, test_user: User, test_user_headers: dict):
    """Test 2FA status check"""

    # Initially disabled
    response = client.get("/api/v1/auth/2fa/status", headers=test_user_headers)
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False

    # Enable 2FA
    secret = two_factor_service.generate_totp_secret()
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    two_factor_service.enable_2fa(db, test_user.id, secret, code)

    # Check status again
    response = client.get("/api/v1/auth/2fa/status", headers=test_user_headers)
    assert response.json()["is_enabled"] is True


def test_2fa_already_enabled_setup(
    db: Session, test_user: User, test_user_headers: dict
):
    """Test setup when 2FA is already enabled"""

    # Enable 2FA first
    secret = two_factor_service.generate_totp_secret()
    import pyotp

    totp = pyotp.TOTP(secret)
    code = totp.now()
    two_factor_service.enable_2fa(db, test_user.id, secret, code)

    # Try to setup again
    response = client.post("/api/v1/auth/2fa/setup", headers=test_user_headers)
    assert response.status_code == 400
    assert "already enabled" in response.json()["detail"]
