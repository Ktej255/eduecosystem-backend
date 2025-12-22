"""
Real-time chat message model for study rooms, groups, and direct messaging.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class PresenceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class RealtimeChatMessage(Base):
    """Model for real-time chat messages."""

    __tablename__ = "realtime_chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)

    # Sender information with use_alter=True to break circular dependency
    sender_id = Column(
        Integer,
        ForeignKey("users.id", use_alter=True, name="fk_chat_sender"),
        nullable=False,
        index=True,
    )
    sender = relationship("User", back_populates="realtime_chat_messages")

    # Target information (one of these should be set)
    study_room_id = Column(Integer, ForeignKey("study_rooms.id"), nullable=True)
    study_group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=True)  # Deprecated
    learning_group_id = Column(Integer, ForeignKey("learning_groups.id"), nullable=True)
    discussion_thread_id = Column(
        Integer, ForeignKey("discussion_threads.id"), nullable=True
    )

    # Relationships
    study_room = relationship("StudyRoom", back_populates="chat_messages")
    study_group = relationship("StudyGroup", back_populates="chat_messages")  # Deprecated
    learning_group = relationship("LearningGroup", backref="chat_messages")

    # Attachments
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(200), nullable=True)
    attachment_size = Column(Integer, nullable=True)  # in bytes

    # Message metadata
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Reactions (stored as JSON string, e.g., '{"👍": [1, 2, 3], "❤️": [4, 5]}')
    reactions = Column(Text, nullable=True)

    # Threading
    parent_id = Column(Integer, ForeignKey("realtime_chat_messages.id"), nullable=True)
    replies = relationship("RealtimeChatMessage", backref="parent", remote_side=[id])

    # Read receipts (JSON array of user IDs who have read this message)
    read_by = Column(Text, nullable=True)  # '{"user_ids": [1, 2, 3], "count": 3}'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RealtimeChatMessage {self.id} from User {self.sender_id}>"


class RealtimeUserPresence(Base):
    """Model for tracking user online/offline/away status."""

    __tablename__ = "realtime_user_presence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", use_alter=True, name="fk_presence_user"),
        unique=True,
        nullable=False,
        index=True,
    )
    user = relationship("User", back_populates="presence")

    # Status
    status = Column(String(20), default="offline")  # online, offline, away, busy

    # Custom status message
    status_message = Column(String(200), nullable=True)

    # Last activity
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Current location in app (e.g., "course:5", "study_room:3")
    current_location = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RealtimeUserPresence {self.user_id}: {self.status}>"
