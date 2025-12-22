from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.services.social_service import social_service

router = APIRouter()


# --- Schemas ---
class UserSchema(BaseModel):
    id: int
    full_name: Optional[str]
    email: str
    model_config = ConfigDict(from_attributes=True)


class FriendRequestResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    receiver_id: int
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    message: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creator_id: int
    is_private: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---


@router.post("/friends/request/{friend_id}", response_model=FriendRequestResponse)
def send_friend_request(
    friend_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Send a friend request"""
    try:
        return social_service.send_friend_request(current_user.id, friend_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/friends/accept/{request_id}", response_model=FriendRequestResponse)
def accept_friend_request(
    request_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Accept a friend request"""
    try:
        return social_service.accept_friend_request(request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/friends", response_model=List[UserSchema])
def get_friends(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get list of friends"""
    return social_service.get_friends(current_user.id)


@router.post("/messages", response_model=MessageResponse)
def send_message(
    msg: MessageCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Send a direct message"""
    return social_service.send_message(current_user.id, msg.receiver_id, msg.content)


@router.get("/conversations/{other_user_id}", response_model=List[MessageResponse])
def get_conversation(
    other_user_id: int,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get conversation history with a user"""
    return social_service.get_conversation(current_user.id, other_user_id, limit)


@router.post("/groups", response_model=GroupResponse)
def create_group(
    group: GroupCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a study group"""
    return social_service.create_group(
        current_user.id, group.name, group.description, group.is_private
    )


@router.get("/groups/my", response_model=List[GroupResponse])
def get_my_groups(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get groups user belongs to"""
    return social_service.get_user_groups(current_user.id)
