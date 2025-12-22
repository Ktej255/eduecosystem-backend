from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.api import deps
from app.models.user import User
from app.services.two_factor_service import two_factor_service
from app.schemas.two_factor import (
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorVerifyResponse,
    TwoFactorStatusResponse,
)

router = APIRouter()


@router.post("/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Initiate 2FA setup. Returns a secret and QR code.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=400, detail="2FA is already enabled for this account."
        )

    secret = two_factor_service.generate_totp_secret()
    uri = two_factor_service.get_totp_uri(current_user.email, secret)
    qr_code = two_factor_service.generate_qr_code(uri)

    return {"secret": secret, "qr_code": qr_code}


@router.post("/verify-setup", response_model=TwoFactorVerifyResponse)
def verify_two_factor_setup(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    data: TwoFactorVerifyRequest,
) -> Any:
    """
    Verify the code and enable 2FA. Returns backup codes.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    if not data.secret:
        raise HTTPException(
            status_code=400, detail="Secret is required for setup verification."
        )

    success = two_factor_service.enable_2fa(db, current_user.id, data.secret, data.code)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid code. Please try again.")

    # Retrieve the newly generated backup codes to show to the user
    backup_codes = two_factor_service.get_backup_codes(db, current_user.id)

    return {
        "success": True,
        "backup_codes": backup_codes,
        "message": "2FA enabled successfully. Please save your backup codes.",
    }


@router.post("/disable", response_model=TwoFactorVerifyResponse)
def disable_two_factor(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    data: TwoFactorVerifyRequest,
) -> Any:
    """
    Disable 2FA. Requires a valid code for security.
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled.")

    # Validate code before disabling
    if not two_factor_service.validate_login(db, current_user.id, data.code):
        raise HTTPException(status_code=400, detail="Invalid code.")

    two_factor_service.disable_2fa(db, current_user.id)

    return {"success": True, "message": "2FA disabled successfully."}


@router.get("/status", response_model=TwoFactorStatusResponse)
def get_two_factor_status(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check if 2FA is enabled.
    """
    return {"is_enabled": current_user.is_2fa_enabled}


from app.schemas.user import Token
from app.core import security
from app.core.config import settings
from datetime import timedelta


@router.post("/verify-login", response_model=Token)
def verify_two_factor_login(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    data: TwoFactorVerifyRequest,
) -> Any:
    """
    Verify 2FA code during login and return full access token.
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user.")

    if not two_factor_service.validate_login(db, current_user.id, data.code):
        raise HTTPException(status_code=400, detail="Invalid code.")

    # Generate full access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            current_user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "require_2fa": False,
    }
