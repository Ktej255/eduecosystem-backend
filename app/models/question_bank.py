from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Boolean,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


# Association table for many-to-many relationship between QuestionBank and Question
question_bank_questions = Table(
    "question_bank_questions",
    Base.metadata,
    Column(
        "question_bank_id", Integer, ForeignKey("question_banks.id"), primary_key=True
    ),
    Column("question_id", Integer, ForeignKey("bank_questions.id"), primary_key=True),
)


class QuestionBank(Base):
    """Reusable pool of questions for random quiz generation"""

    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Categorization
    category = Column(String(100), nullable=True)  # e.g., "Chapter 1", "Midterm", etc.
    difficulty_level = Column(String(20), default="medium")  # easy, medium, hard

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", backref="question_banks")
    instructor = relationship("User", backref="question_banks")
    questions = relationship(
        "BankQuestion",
        secondary=question_bank_questions,
        back_populates="question_banks",
    )


class BankQuestion(Base):
    """Questions stored in question banks"""

    __tablename__ = "bank_questions"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # multiple_choice, true_false, etc.
    points = Column(Integer, default=1)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard

    # Question content (JSON)
    options = Column(Text, nullable=True)  # JSON string for multiple choice options
    correct_answer = Column(Text, nullable=True)  # For short answer, true/false
    explanation = Column(Text, nullable=True)

    # Metadata
    tags = Column(Text, nullable=True)  # Comma-separated tags
    usage_count = Column(Integer, default=0)  # How many times used in quizzes

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    instructor = relationship("User", backref="bank_questions")
    question_banks = relationship(
        "QuestionBank", secondary=question_bank_questions, back_populates="questions"
    )


class QuizQuestionPool(Base):
    """Configuration for random question selection from question banks"""

    __tablename__ = "quiz_question_pools"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=False)

    # Selection criteria
    num_questions = Column(Integer, nullable=False)  # How many questions to select
    difficulty_filter = Column(String(20), nullable=True)  # Filter by difficulty

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz = relationship("Quiz", backref="question_pools")
    question_bank = relationship("QuestionBank", backref="quiz_pools")
