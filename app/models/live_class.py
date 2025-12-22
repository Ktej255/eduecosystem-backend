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


class LiveClassStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LiveClass(Base):
    """
    Live class/webinar session model.
    Represents scheduled or on-demand live sessions for a course.
    """

    __tablename__ = "live_classes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic info
    title = Column(String, nullable=False)
    description = Column(Text)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)

    # Meeting details
    meeting_url = Column(String)  # Zoom/Meet link or custom WebRTC room ID
    meeting_password = Column(String)
    platform = Column(String, default="zoom")  # 'zoom', 'meet', 'webrtc', 'custom'

    # Status
    status = Column(
        SQLEnum(LiveClassStatus), default=LiveClassStatus.SCHEDULED, index=True
    )

    # Recording (if available)
    recording_url = Column(String)
    recording_available = Column(Boolean, default=False)

    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Whiteboard state
    whiteboard_data = Column(JSON, default=dict)

    # Relationships
    course = relationship("Course", backref="live_classes")
    instructor = relationship("User", foreign_keys=[instructor_id])
    attendance_records = relationship(
        "LiveClassAttendance", back_populates="live_class", cascade="all, delete-orphan"
    )

    # Interactive features (Phase 5)
    polls = relationship(
        "LiveClassPoll", back_populates="live_class", cascade="all, delete-orphan"
    )
    questions = relationship(
        "LiveClassQuestion", back_populates="live_class", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "LiveClassChatMessage",
        back_populates="live_class",
        cascade="all, delete-orphan",
    )
    reactions = relationship(
        "LiveClassReaction", back_populates="live_class", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LiveClass {self.title} - {self.status}>"


class LiveClassAttendance(Base):
    """
    Tracks student attendance for live classes.
    """

    __tablename__ = "live_class_attendance"

    id = Column(Integer, primary_key=True, index=True)
    live_class_id = Column(
        Integer,
        ForeignKey("live_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Attendance tracking
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    left_at = Column(DateTime)
    duration_minutes = Column(Integer)  # Calculated duration

    # Engagement metrics (optional)
    asked_questions = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    live_class = relationship("LiveClass", back_populates="attendance_records")
    student = relationship("User", foreign_keys=[student_id])

    def __repr__(self):
        return f"<Attendance {self.student_id} - LiveClass {self.live_class_id}>"
