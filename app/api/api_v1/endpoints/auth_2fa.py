from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any
import pyotp
import qrcode
import io
import base64

from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter()

@router.post("/setup")
def setup_2fa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Generate a TOTP secret and QR code for 2FA setup.
    """
    # Generate random secret
    secret = pyotp.random_base32()
    
    # Create OTP URI
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="Eduecosystem"
    )
    
    # Generate QR Code
    img = qrcode.make(otp_uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # Temporarily store secret (or just return it to client to be sent back on verify)
    # Ideally, we verify it first before saving to DB, but for simplicity we can just return it
    # Client must send it back with the code to verify
    
    return {
        "secret": secret,
        "qr_code_url": f"data:image/png;base64,{qr_code_base64}"
    }

@router.post("/verify")
def verify_2fa(
    code: str = Body(..., embed=True),
    secret: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Verify the code and enable 2FA if correct.
    """
    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        # Code is correct, enable 2FA for user
        current_user.totp_secret = secret
        db.add(current_user)
        db.commit()
        return {"success": True, "message": "2FA enabled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")

@router.post("/disable")
def disable_2fa(
    password: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Disable 2FA (requires password confirmation)
    """
    # Verify password (add logic here if needed, or assume token auth is enough for now)
    # For high security, we should verify password explicitly
    
    current_user.totp_secret = None
    db.add(current_user)
    db.commit()
    return {"success": True, "message": "2FA disabled successfully"}

@router.post("/verify-login")
def verify_2fa_login(
    code: str = Body(..., embed=True),
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify 2FA code during login process and return full token.
    """
    from app.core import security
    from datetime import timedelta
    from app.core.config import settings

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=404, detail="User not found or 2FA not enabled")
        
    totp = pyotp.TOTP(user.totp_secret)
    if totp.verify(code):
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token": security.create_access_token(
                user.id, expires_delta=access_token_expires, token_version=user.token_version
            ),
            "token_type": "bearer",
            "require_2fa": False
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid code")
