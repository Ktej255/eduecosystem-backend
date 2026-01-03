from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    email_notifications: Optional[bool] = True
    is_premium: Optional[bool] = False
    subscription_status: Optional[str] = "free"
    is_ras_authorized: bool = False
    is_batch1_authorized: bool = False
    is_batch2_authorized: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: Optional[str] = None
    password: str
    role: Optional[str] = "student"


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    require_2fa: Optional[bool] = False


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class UserBasic(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)


class UserWithToken(User):
    access_token: str
    token_type: str

