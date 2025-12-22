from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from datetime import datetime
import enum


class ProgressStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status
    status = Column(
        SQLEnum(ProgressStatus), default=ProgressStatus.NOT_STARTED, index=True
    )

    # Time tracking
    time_spent_seconds = Column(Integer, default=0)
    first_accessed_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Video progress (for video lessons)
    video_progress_seconds = Column(Integer, default=0)
    video_completed_percentage = Column(Float, default=0.0)

    # Quiz/Assignment results
    result_data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    lesson = relationship("Lesson", back_populates="progress_records")

    def __repr__(self):
        return f"<LessonProgress user_id={self.user_id} lesson_id={self.lesson_id} status={self.status}>"
