from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class LessonDripSetting(Base):
    """
    Content Drip settings for lessons.
    Controls when lessons become available to students.
    """

    __tablename__ = "lesson_drip_settings"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Unlock type: 'date', 'sequence', 'after_days'
    unlock_type = Column(String(20), nullable=False)

    # Date-based unlock
    unlock_date = Column(DateTime, nullable=True)

    # Days after enrollment
    unlock_after_days = Column(Integer, nullable=True)

    # Sequence-based (prerequisite)
    prerequisite_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    # Active status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lesson = relationship(
        "Lesson", foreign_keys=[lesson_id], back_populates="drip_setting"
    )
    prerequisite_lesson = relationship("Lesson", foreign_keys=[prerequisite_lesson_id])
