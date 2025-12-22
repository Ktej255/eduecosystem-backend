from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.user import User


class FriendshipBase(BaseModel):
    receiver_id: int


class FriendshipCreate(FriendshipBase):
    pass


class FriendshipUpdate(BaseModel):
    status: str


class Friendship(FriendshipBase):
    id: int
    sender_id: int
    status: str
    created_at: datetime
    sender: Optional[User] = None
    receiver: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)
