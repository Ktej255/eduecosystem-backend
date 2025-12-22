from sqlalchemy import (
    Column,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status
    status = Column(
        SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, index=True
    )

    # Progress tracking
    progress_percentage = Column(Float, default=0.0)  # 0-100
    last_accessed_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    # Timestamps
    enrolled_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # For time-limited access
    last_accessed_at = Column(DateTime, default=datetime.utcnow)

    # Payment info (if applicable)
    payment_id = Column(Integer, nullable=True)  # Reference to payment record
    price_paid = Column(Float, default=0.0)

    # Certificate
    certificate_issued = Column(Boolean, default=False)
    certificate_issued_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    certificate = relationship(
        "Certificate", back_populates="enrollment", uselist=False
    )
    last_accessed_lesson = relationship(
        "Lesson", foreign_keys=[last_accessed_lesson_id]
    )

    def __repr__(self):
        return f"<Enrollment user_id={self.user_id} course_id={self.course_id}>"
