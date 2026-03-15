from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base

class Assignment(Base):
    __tablename__ = "lms_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id"))
    rubric_json = Column(JSON, nullable=True) # Grading Rubric
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    batch = relationship("UPSCBatch", backref="lms_assignments")
    submissions = relationship("StudentSubmission", back_populates="assignment", cascade="all, delete-orphan")

class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"
    PUBLISHED = "published"

class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("lms_assignments.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    
    content_text = Column(Text, nullable=True)
    s3_pdf_url = Column(String, nullable=True)
    status = Column(String, default="pending") # pending, submitted, evaluated, published
    
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", backref="lms_submissions")
    evaluation_logs = relationship("AIEvaluationLog", back_populates="submission", cascade="all, delete-orphan")

class EvaluationStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class AIEvaluationLog(Base):
    __tablename__ = "ai_evaluation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("student_submissions.id"))
    
    ai_score = Column(Float, nullable=True)
    ai_feedback_json = Column(JSON, nullable=True) # Score, Strengths, Weaknesses, Directive Feedback
    teacher_approved_score = Column(Float, nullable=True)
    status = Column(String, default="draft") # draft, published
    
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submission = relationship("StudentSubmission", back_populates="evaluation_logs")

class Question(Base):
    __tablename__ = "lms_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    subject_tag = Column(String, nullable=True, index=True)
    difficulty = Column(String, default="medium")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("User", backref="lms_questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")

class Option(Base):
    __tablename__ = "lms_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("lms_questions.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    # Relationships
    question = relationship("Question", back_populates="options")
