from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
    DateTime,
    Float,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime, timezone


def utcnow():
    """
    Utility function for timezone-aware datetime defaults compatible with SQLite.
    Returns timezone-naive UTC datetime (SQLite requirement) generated using modern API.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LearningPath(Base):
    """
    Learning Path model representing a sequence of courses.
    Allows bundling multiple courses into a structured learning journey.
    """

    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    slug = Column(String, unique=True, index=True)

    # Visual
    thumbnail_url = Column(String)
    cover_image_url = Column(String)

    # Difficulty and metadata
    difficulty_level = Column(
        String, default="beginner"
    )  # beginner, intermediate, advanced
    estimated_duration_hours = Column(Integer)  # Total hours for the entire path

    # Pricing (optional - can be free)
    price = Column(Float, default=0.0)

    # Publishing
    is_published = Column(Boolean, default=False)

    # Creator
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    path_courses = relationship(
        "PathCourse",
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="PathCourse.order_index",
    )
    enrollments = relationship(
        "PathEnrollment", back_populates="path", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LearningPath {self.title}>"


class PathCourse(Base):
    """
    Represents a course within a learning path with ordering and prerequisites.
    """

    __tablename__ = "path_courses"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(
        Integer,
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Ordering
    order_index = Column(Integer, default=0, index=True)

    # Prerequisites (course that must be completed before this one)
    prerequisite_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

    # Metadata
    is_required = Column(Boolean, default=True)  # Some courses might be optional

    # Timestamps
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    path = relationship("LearningPath", back_populates="path_courses")
    course = relationship("Course", foreign_keys=[course_id])
    prerequisite_course = relationship("Course", foreign_keys=[prerequisite_course_id])

    def __repr__(self):
        return f"<PathCourse {self.path_id} - Course {self.course_id}>"


class PathEnrollment(Base):
    """
    Tracks student enrollment and progress in a learning path.
    """

    __tablename__ = "path_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(
        Integer,
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Progress tracking
    current_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    completed_courses = Column(Integer, default=0)
    total_courses = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Payment tracking (if path has a price)
    has_paid = Column(Boolean, default=False)
    payment_id = Column(Integer, ForeignKey("course_payments.id"), nullable=True)

    # Timestamps
    enrolled_at = Column(DateTime, default=utcnow)
    last_accessed_at = Column(DateTime, default=utcnow)

    # Relationships
    path = relationship("LearningPath", back_populates="enrollments")
    student = relationship("User", foreign_keys=[student_id])
    current_course = relationship("Course", foreign_keys=[current_course_id])
    payment = relationship("CoursePayment", foreign_keys=[payment_id])

    def __repr__(self):
        return f"<PathEnrollment {self.student_id} - Path {self.path_id}>"
