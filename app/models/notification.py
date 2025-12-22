from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    Text,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from datetime import datetime
import enum


class NotificationType(str, enum.Enum):
    """Notification type categories"""

    # Academic
    COURSE_ENROLLED = "course_enrolled"
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_GRADED = "assignment_graded"
    CERTIFICATE_ISSUED = "certificate_issued"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"

    # Instructor
    STUDENT_ENROLLED = "student_enrolled"
    ASSIGNMENT_SUBMITTED = "assignment_submitted"
    COURSE_REVIEW = "course_review"
    DISCUSSION_REPLY = "discussion_reply"

    # Social
    FRIEND_REQUEST = "friend_request"
    GROUP_INVITATION = "group_invitation"
    MENTION = "mention"

    # System
    SYSTEM_ANNOUNCEMENT = "system_announcement"

    # Real-time (Phase 5)
    LIVE_CLASS_STARTING = "live_class_starting"
    DIRECT_MESSAGE = "direct_message"
    COMMENT_REPLY = "comment_reply"
    BADGE_EARNED = "badge_earned"

    # UPSC Module
    UPSC_PLAN_GENERATED = "upsc_plan_generated"
    UPSC_REPORT_READY = "upsc_report_ready"
    UPSC_DRILL_REMINDER = "upsc_drill_reminder"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification content
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Additional context data (JSON)
    data = Column(JSON, default=dict)  # e.g., {"course_id": 1, "assignment_id": 5}

    # Link to navigate when clicked
    action_url = Column(String(500), nullable=True)

    # Priority (Phase 5)
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, index=True
    )

    # Status
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Real-time delivery tracking (Phase 5)
    delivered_realtime = Column(Boolean, default=False)
    delivered_push = Column(Boolean, default=False)
    delivered_email = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} - {self.type} for user {self.user_id}>"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def mark_delivered_realtime(self):
        """Mark as delivered via WebSocket"""
        self.delivered_realtime = True

    def mark_delivered_push(self):
        """Mark as delivered via push notification"""
        self.delivered_push = True

    def mark_delivered_email(self):
        """Mark as delivered via email"""
        self.delivered_email = True
