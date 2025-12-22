from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CourseAnnouncement(Base):
    """Announcements posted by instructors for course students"""

    __tablename__ = "course_announcements"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # Settings
    is_pinned = Column(Boolean, default=False)  # Show at top
    is_published = Column(Boolean, default=True)
    send_notification = Column(Boolean, default=True)  # Send push notification
    send_email = Column(Boolean, default=False)  # Send email notification

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    course = relationship("Course", backref="announcements")
    instructor = relationship(
        "User", foreign_keys=[instructor_id], backref="course_announcements"
    )


class AnnouncementRead(Base):
    """Track which students have read which announcements"""

    __tablename__ = "announcement_reads"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(
        Integer, ForeignKey("course_announcements.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    read_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    announcement = relationship("CourseAnnouncement", backref="reads")
    user = relationship("User", backref="announcement_reads")

    # Unique constraint: one read record per user per announcement
    __table_args__ = ({"sqlite_autoincrement": True},)
