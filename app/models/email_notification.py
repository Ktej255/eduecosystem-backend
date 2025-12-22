from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import enum


class NotificationType(str, enum.Enum):
    ENROLLMENT = "enrollment"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    ASSIGNMENT_GRADED = "assignment_graded"
    QUIZ_COMPLETED = "quiz_completed"
    QUIZ_GRADED = "quiz_graded"
    CERTIFICATE_EARNED = "certificate_earned"
    ANNOUNCEMENT = "announcement"
    REVIEW_RECEIVED = "review_received"
    COURSE_UPDATED = "course_updated"
    GENERAL = "general"


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class UserEmailPreference(Base):
    __tablename__ = "user_email_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Individual notification preferences
    enrollment_enabled = Column(Boolean, default=True)
    assignment_enabled = Column(Boolean, default=True)
    quiz_enabled = Column(Boolean, default=True)
    certificate_enabled = Column(Boolean, default=True)
    announcement_enabled = Column(Boolean, default=True)
    review_enabled = Column(Boolean, default=True)
    course_update_enabled = Column(Boolean, default=True)
    general_enabled = Column(Boolean, default=True)

    # Master switch
    all_emails_enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="email_preferences")

    def is_enabled(self, notification_type: NotificationType) -> bool:
        """Check if a specific notification type is enabled"""
        if not self.all_emails_enabled:
            return False

        type_mapping = {
            NotificationType.ENROLLMENT: self.enrollment_enabled,
            NotificationType.ASSIGNMENT_SUBMITTED: self.assignment_enabled,
            NotificationType.ASSIGNMENT_GRADED: self.assignment_enabled,
            NotificationType.QUIZ_COMPLETED: self.quiz_enabled,
            NotificationType.QUIZ_GRADED: self.quiz_enabled,
            NotificationType.CERTIFICATE_EARNED: self.certificate_enabled,
            NotificationType.ANNOUNCEMENT: self.announcement_enabled,
            NotificationType.REVIEW_RECEIVED: self.review_enabled,
            NotificationType.COURSE_UPDATED: self.course_update_enabled,
            NotificationType.GENERAL: self.general_enabled,
        }
        return type_mapping.get(notification_type, True)


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String, unique=True, nullable=False, index=True
    )  # e.g., "course_enrollment"
    display_name = Column(String, nullable=False)  # User-friendly name
    subject = Column(String, nullable=False)  # Can include {{variables}}
    body_html = Column(Text, nullable=False)  # HTML version with {{variables}}
    body_text = Column(Text, nullable=True)  # Plain text fallback
    variables = Column(
        JSON, default=list
    )  # List of available variables: ["student_name", "course_title"]

    is_system = Column(Boolean, default=False)  # System templates cannot be deleted
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)

    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    email_logs = relationship(
        "EmailLog", back_populates="template", cascade="all, delete-orphan"
    )


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id = Column(
        Integer, ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True
    )

    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, index=True)

    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Store rendered content for audit trail
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    template = relationship("EmailTemplate", back_populates="email_logs")
