from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud_user.get(db, id=token_data.sub)
    if not user:
        # print(f"DEBUG: User not found for id {token_data.sub}")
        raise HTTPException(status_code=404, detail="User not found")

    # Verify Token Version
    token_version = payload.get("v", 1)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Logged in from another device.",
        )

    return user


reusable_oauth2_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token", auto_error=False
)


def get_current_user_optional(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2_optional)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        return None

    user = crud_user.get(db, id=token_data.sub)
    if not user:
        return None

    # Verify Token Version
    token_version = payload.get("v", 1)
    if token_version != user.token_version:
        return None

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if current_user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")
    return current_user


def get_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != "admin" and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized. Admin access required."
        )
    return current_user


def get_current_instructor(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if (
        current_user.role != "instructor"
        and current_user.role != "admin"
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized. Instructor access required."
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current active superuser. Used for routes that require superuser access."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized. Superuser access required."
        )
    return current_user


import logging
from starlette.concurrency import run_in_threadpool
logger = logging.getLogger(__name__)

async def get_current_user_ws(token: str, db: Session) -> User:
    """
    Get current user from WebSocket token.
    Used for WebSocket endpoint authentication.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # Run sync DB operation in threadpool to avoid blocking event loop
    user = await run_in_threadpool(crud_user.get, db, id=token_data.sub)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify Token Version
    token_version = payload.get("v", 1)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Logged in from another device.",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")

    return user


get_current_admin = get_admin_user
get_current_superuser = get_current_active_superuser
