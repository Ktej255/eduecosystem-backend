"""
Interactive models for Live Classes (Polls, Q&A, Reactions, Chat)
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum


class PollStatus(str, enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    ENDED = "ended"


class LiveClassPoll(Base):
    """Polls created during a live class"""

    __tablename__ = "live_class_polls"

    id = Column(Integer, primary_key=True, index=True)
    live_class_id = Column(
        Integer,
        ForeignKey("live_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # List of strings
    correct_option_index = Column(Integer, nullable=True)  # Optional correct answer

    status = Column(SQLEnum(PollStatus), default=PollStatus.CREATED)

    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    live_class = relationship("LiveClass", back_populates="polls")
    responses = relationship(
        "LiveClassPollResponse", back_populates="poll", cascade="all, delete-orphan"
    )


class LiveClassPollResponse(Base):
    """Student responses to polls"""

    __tablename__ = "live_class_poll_responses"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(
        Integer,
        ForeignKey("live_class_polls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    selected_option_index = Column(Integer, nullable=False)
    responded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    poll = relationship("LiveClassPoll", back_populates="responses")
    student = relationship("User", foreign_keys=[student_id])


class LiveClassQuestion(Base):
    """Q&A questions asked by students"""

    __tablename__ = "live_class_questions"

    id = Column(Integer, primary_key=True, index=True)
    live_class_id = Column(
        Integer,
        ForeignKey("live_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    question_text = Column(Text, nullable=False)
    is_answered = Column(Boolean, default=False)
    answer_text = Column(Text, nullable=True)

    upvotes = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)

    # Relationships
    live_class = relationship("LiveClass", back_populates="questions")
    student = relationship("User", foreign_keys=[student_id])


class LiveClassReaction(Base):
    """Real-time reactions (emojis)"""

    __tablename__ = "live_class_reactions"

    id = Column(Integer, primary_key=True, index=True)
    live_class_id = Column(
        Integer,
        ForeignKey("live_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    reaction_type = Column(String, nullable=False)  # e.g., 'thumbs_up', 'heart', 'clap'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    live_class = relationship("LiveClass", back_populates="reactions")
    student = relationship("User", foreign_keys=[student_id])


class LiveClassChatMessage(Base):
    """Chat messages during live class"""

    __tablename__ = "live_class_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    live_class_id = Column(
        Integer,
        ForeignKey("live_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    message = Column(Text, nullable=False)
    is_instructor = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    live_class = relationship("LiveClass", back_populates="chat_messages")
    user = relationship("User", foreign_keys=[user_id])
