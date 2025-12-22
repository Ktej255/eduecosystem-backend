from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Text, DECIMAL, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
import uuid

from app.db.base import Base

class UPSCBatch(Base):
    __tablename__ = "upsc_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    plans = relationship("UPSCPlan", back_populates="batch", cascade="all, delete-orphan")
    drills = relationship("UPSCDrill", back_populates="batch", cascade="all, delete-orphan")
    timer_configs = relationship("UPSCTimerConfig", back_populates="batch", cascade="all, delete-orphan")
    rubrics = relationship("UPSCRubric", back_populates="batch", cascade="all, delete-orphan")
    student_profiles = relationship("UPSCStudentProfile", back_populates="batch", cascade="all, delete-orphan")

class UPSCStudentProfile(Base):
    __tablename__ = "upsc_student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id"))
    enrollment_date = Column(Date, nullable=False)
    target_year = Column(Integer)
    preferred_language = Column(String, default="english")
    profile_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User", backref="upsc_profile")
    batch = relationship("UPSCBatch", back_populates="student_profiles")

class UPSCPlan(Base):
    __tablename__ = "upsc_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id", ondelete="CASCADE"))
    plan_type = Column(String, nullable=False) # monthly, weekly, daily
    parent_plan_id = Column(UUID(as_uuid=True), ForeignKey("upsc_plans.id"), nullable=True)
    title = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    ai_generated = Column(Boolean, default=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    version = Column(Integer, default=1)
    plan_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    batch = relationship("UPSCBatch", back_populates="plans")
    parent_plan = relationship("UPSCPlan", remote_side=[id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    questions = relationship("UPSCQuestion", back_populates="plan", cascade="all, delete-orphan")
    student_progress = relationship("UPSCStudentProgress", back_populates="plan", cascade="all, delete-orphan")

class UPSCQuestion(Base):
    __tablename__ = "upsc_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("upsc_plans.id", ondelete="CASCADE"))
    question_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    marks = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String)
    microtopics = Column(JSON, nullable=False)
    keywords = Column(JSON)
    pyq_reference = Column(String)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    plan = relationship("UPSCPlan", back_populates="questions")
    created_by = relationship("User", foreign_keys=[created_by_id])
    content = relationship("UPSCContent", back_populates="question", cascade="all, delete-orphan")
    attempts = relationship("UPSCAttempt", back_populates="question", cascade="all, delete-orphan")

class UPSCContent(Base):
    __tablename__ = "upsc_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("upsc_questions.id", ondelete="CASCADE"))
    content_type = Column(String, nullable=False) # one_pager, model_answer, pdf, reference
    title = Column(String)
    content_text = Column(Text)
    file_url = Column(String)
    microtopics = Column(JSON)
    keywords = Column(JSON)
    current_affairs = Column(JSON)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    question = relationship("UPSCQuestion", back_populates="content")
    created_by = relationship("User", foreign_keys=[created_by_id])

class UPSCDrill(Base):
    __tablename__ = "upsc_drills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id", ondelete="CASCADE"))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("upsc_plans.id"))
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled")
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    batch = relationship("UPSCBatch", back_populates="drills")
    plan = relationship("UPSCPlan")
    created_by = relationship("User", foreign_keys=[created_by_id])

class UPSCStudentProgress(Base):
    __tablename__ = "upsc_student_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("upsc_plans.id", ondelete="CASCADE"))
    is_locked = Column(Boolean, default=True)
    unlocked_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    completion_percentage = Column(DECIMAL(5,2), default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    student = relationship("User", foreign_keys=[student_id])
    plan = relationship("UPSCPlan", back_populates="student_progress")
    
    __table_args__ = (UniqueConstraint('student_id', 'plan_id', name='_student_plan_uc'),)

class UPSCAttempt(Base):
    __tablename__ = "upsc_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("upsc_questions.id", ondelete="CASCADE"))
    attempt_type = Column(String, nullable=False) # before, after
    answer_text = Column(Text)
    image_url = Column(String)
    audio_url = Column(String)
    transcription = Column(Text)
    word_count = Column(Integer)
    time_taken_seconds = Column(Integer)
    ocr_confidence = Column(DECIMAL(5,2))
    submitted_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    drill_session_id = Column(UUID(as_uuid=True))

    student = relationship("User", foreign_keys=[student_id])
    question = relationship("UPSCQuestion", back_populates="attempts")
    
    # Relationships for reports (defined here to avoid circular dependency issues if possible, or use string)
    reports_as_before = relationship("UPSCReport", foreign_keys="[UPSCReport.attempt_before_id]", back_populates="attempt_before")
    reports_as_after = relationship("UPSCReport", foreign_keys="[UPSCReport.attempt_after_id]", back_populates="attempt_after")

class UPSCReport(Base):
    __tablename__ = "upsc_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_before_id = Column(UUID(as_uuid=True), ForeignKey("upsc_attempts.id", ondelete="CASCADE"))
    attempt_after_id = Column(UUID(as_uuid=True), ForeignKey("upsc_attempts.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("upsc_questions.id", ondelete="CASCADE"))

    coverage_before = Column(DECIMAL(5,2))
    similarity_before = Column(DECIMAL(5,2))
    keyword_recall_before = Column(DECIMAL(5,2))
    structure_score_before = Column(DECIMAL(5,2))
    language_score_before = Column(DECIMAL(5,2))
    estimated_marks_before = Column(DECIMAL(5,2))

    coverage_after = Column(DECIMAL(5,2))
    similarity_after = Column(DECIMAL(5,2))
    keyword_recall_after = Column(DECIMAL(5,2))
    structure_score_after = Column(DECIMAL(5,2))
    language_score_after = Column(DECIMAL(5,2))
    estimated_marks_after = Column(DECIMAL(5,2))

    missed_points = Column(JSON)
    suggestions = Column(JSON)
    common_mistakes = Column(JSON)
    tone_feedback = Column(Text)

    ai_model_version = Column(String)
    raw_ai_output = Column(JSON)
    
    generated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))

    attempt_before = relationship("UPSCAttempt", foreign_keys=[attempt_before_id], back_populates="reports_as_before")
    attempt_after = relationship("UPSCAttempt", foreign_keys=[attempt_after_id], back_populates="reports_as_after")
    student = relationship("User", foreign_keys=[student_id])
    question = relationship("UPSCQuestion")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

class UPSCTimerConfig(Base):
    __tablename__ = "upsc_timer_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id"))
    phase = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    batch = relationship("UPSCBatch", back_populates="timer_configs")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    __table_args__ = (UniqueConstraint('batch_id', 'phase', name='_batch_phase_uc'),)

class UPSCRubric(Base):
    __tablename__ = "upsc_rubrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("upsc_batches.id"))
    subject = Column(String)
    rubric_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    batch = relationship("UPSCBatch", back_populates="rubrics")
    created_by = relationship("User", foreign_keys=[created_by_id])
