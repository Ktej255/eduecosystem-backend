from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class SubmissionStatus(str, enum.Enum):
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    GRADED = "graded"
    LATE = "late"


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    # Grading
    max_points = Column(Float, default=100.0)

    # Deadlines
    due_date = Column(DateTime, nullable=True)
    allow_late_submission = Column(Boolean, default=True)
    late_penalty_per_day = Column(Float, default=0.0)  # Percentage (0-100)

    # Settings
    is_published = Column(Boolean, default=False)
    file_upload_required = Column(Boolean, default=True)
    allowed_file_types = Column(
        JSON, default=list
    )  # List of extensions: [".pdf", ".docx"]
    max_file_size_mb = Column(Integer, default=50)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    course = relationship("Course", backref="assignments")
    lesson = relationship("Lesson", back_populates="assignment")
    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Submission content
    submitted_files = Column(JSON, default=list)  # List of file paths
    notes = Column(Text, nullable=True)  # Student's submission notes

    # Grading
    grade = Column(Float, nullable=True)  # Points awarded
    feedback = Column(Text, nullable=True)  # Instructor feedback
    status = Column(String, default=SubmissionStatus.NOT_SUBMITTED)

    # Timestamps
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", back_populates="assignment_submissions")
    plagiarism_checks = relationship(
        "PlagiarismCheck", back_populates="submission", cascade="all, delete-orphan"
    )
