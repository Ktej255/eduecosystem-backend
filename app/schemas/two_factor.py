from typing import Optional, List
from pydantic import BaseModel


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str  # Base64 encoded image


class TwoFactorVerifyRequest(BaseModel):
    secret: Optional[str] = None  # Used during setup
    code: str


class TwoFactorVerifyResponse(BaseModel):
    success: bool
    backup_codes: Optional[List[str]] = None
    message: str


class TwoFactorLoginRequest(BaseModel):
    user_id: int
    code: str


class TwoFactorStatusResponse(BaseModel):
    is_enabled: bool
