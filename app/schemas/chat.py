"""
Pydantic schemas for real-time chat and presence features.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


# Chat Message Schemas


class ChatMessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    study_room_id: Optional[int] = None
    study_group_id: Optional[int] = None
    discussion_thread_id: Optional[int] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    parent_id: Optional[int] = None


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    is_edited: Optional[bool] = None
    is_deleted: Optional[bool] = None


class Reaction(BaseModel):
    emoji: str
    user_ids: List[int] = []
    count: int = 0


class ChatMessageResponse(ChatMessageBase):
    id: int
    sender_id: int
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    created_at: datetime
    reactions: Optional[List[Reaction]] = []
    read_by_count: int = 0
    reply_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChatMessageList(BaseModel):
    messages: List[ChatMessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# User Presence Schemas


class PresenceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class UserPresenceBase(BaseModel):
    status: PresenceStatus = PresenceStatus.ONLINE
    status_message: Optional[str] = None
    current_location: Optional[str] = None


class UserPresenceUpdate(BaseModel):
    status: Optional[PresenceStatus] = None
    status_message: Optional[str] = None
    current_location: Optional[str] = None


class UserPresenceResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    last_seen: datetime
    current_location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# WebSocket Message Schemas


class WSMessage(BaseModel):
    """Base WebSocket message schema."""

    type: str
    data: dict = {}


class WSChatMessage(BaseModel):
    """WebSocket chat message."""

    type: str = "chat_message"
    message: ChatMessageResponse


class WSTypingIndicator(BaseModel):
    """WebSocket typing indicator."""

    type: str = "typing"
    user_id: int
    user_name: str
    is_typing: bool


class WSPresenceUpdate(BaseModel):
    """WebSocket presence update."""

    type: str = "presence_update"
    user_id: int
    status: PresenceStatus
    last_seen: datetime


class WSOnlineUsers(BaseModel):
    """WebSocket online users list."""

    type: str = "online_users"
    users: List[UserPresenceResponse]
    count: int


# Read Receipt Schemas


class ReadReceiptCreate(BaseModel):
    message_id: int


class ReadReceiptResponse(BaseModel):
    message_id: int
    read_by_count: int
    read_by_users: List[
        dict
    ] = []  # [{"user_id": 1, "user_name": "John", "read_at": "2024-..."}, ...]


# Reaction Schemas


class ReactionCreate(BaseModel):
    message_id: int
    emoji: str


class ReactionRemove(BaseModel):
    message_id: int
    emoji: str


class ReactionResponse(BaseModel):
    message_id: int
    reactions: List[Reaction]
    total_reactions: int
