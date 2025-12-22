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


class LessonType(str, enum.Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    INTERACTIVE = "interactive"
    LIVE_CLASS = "live_class"
    DOWNLOAD = "download"


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(
        Integer,
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String, nullable=False)
    description = Column(Text)

    # Lesson type determines how content is rendered
    type = Column(SQLEnum(LessonType), default=LessonType.TEXT, index=True)

    # Flexible content storage (stores different data based on type)
    # For TEXT: {"markdown": "..."}
    # For VIDEO: {"video_url": "...", "transcript": "..."}
    # For QUIZ: {"quiz_id": 123}
    # For INTERACTIVE: {"h5p_content": {...}}
    content = Column(JSON, default=dict)

    # Video-specific fields (for VIDEO type)
    video_url = Column(String, nullable=True)
    video_duration_seconds = Column(Integer, nullable=True)

    # Video hosting metadata
    video_provider = Column(
        String, default="local"
    )  # 'local', 'cloudflare', 'youtube', 'vimeo'
    video_id = Column(String, nullable=True)  # Provider-specific ID
    video_thumbnail_url = Column(String, nullable=True)

    # Processing status
    video_status = Column(
        String, default="ready"
    )  # 'uploading', 'processing', 'ready', 'error'
    video_uploaded_at = Column(DateTime, nullable=True)

    # Attachments (PDFs, files, etc.)
    attachments = Column(
        JSON, default=list
    )  # [{"name": "...", "url": "...", "size": ...}]

    # Ordering
    order_index = Column(Integer, default=0, index=True)

    # Access control
    is_preview = Column(Boolean, default=False)  # Free preview lesson

    # Content drip settings
    available_after_days = Column(Integer, default=0)  # Days after enrollment to unlock
    prerequisite_lesson_ids = Column(JSON, default=list)  # Must complete these first

    # Metadata
    duration_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    module = relationship("Module", back_populates="lessons")
    progress_records = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan"
    )
    assignment = relationship(
        "Assignment",
        back_populates="lesson",
        uselist=False,
        cascade="all, delete-orphan",
    )
    drip_setting = relationship(
        "LessonDripSetting",
        back_populates="lesson",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="LessonDripSetting.lesson_id",
    )

    def __repr__(self):
        return f"<Lesson {self.title} ({self.type})>"
