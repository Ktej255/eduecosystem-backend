"""
AI-Powered Features Models

Models for storing AI-generated content, grading results, embeddings, and plagiarism checks.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class ContentEmbedding(Base):
    """
    Store embeddings for content (courses, lessons, quizzes) for semantic search.
    """

    __tablename__ = "content_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, nullable=False, index=True)
    content_type = Column(
        String(50), nullable=False
    )  # 'course', 'lesson', 'quiz', 'assignment'
    embedding_model = Column(String(50), default="text-embedding-ada-002")
    embedding_dimension = Column(Integer, default=1536)
    # Store as JSON for PostgreSQL compatibility (or use vector extension)
    embedding_vector = Column(JSON, nullable=False)

    # Metadata
    content_title = Column(String(500))
    content_excerpt = Column(Text)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlagiarismCheck(Base):
    """
    Track plagiarism detection results for student submissions.
    """

    __tablename__ = "plagiarism_checks"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Results
    similarity_percentage = Column(Float, nullable=False)  # 0-100
    originality_score = Column(Float, nullable=False)  # 0-100
    matches = Column(JSON)  # List of matched sources
    """
    matches format:
    [
        {
            "source": "Wikipedia",
            "url": "https://...",
            "percentage": 8.5,
            "text_snippet": "...",
            "matched_phrases": ["...", "..."]
        }
    ]
    """

    # Flags
    is_plagiarized = Column(Boolean, default=False)  # True if similarity > threshold
    review_required = Column(Boolean, default=False)
    reviewed_by_instructor = Column(Boolean, default=False)
    instructor_notes = Column(Text)

    # Metadata
    check_method = Column(String(50), default="ai")  # 'ai', 'turnitin', 'manual'
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="plagiarism_checks")


class AIGeneratedQuiz(Base):
    """
    Store AI-generated quizzes with metadata.
    """

    __tablename__ = "ai_generated_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = Column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    quiz_id = Column(
        Integer, ForeignKey("quizzes.id", ondelete="SET NULL")
    )  # If converted to real quiz

    # Generation parameters
    source_content = Column(Text, nullable=False)  # Content used for generation
    difficulty_level = Column(String(20), default="medium")  # 'easy', 'medium', 'hard'
    num_questions = Column(Integer, nullable=False)
    question_types = Column(JSON)  # ['mcq', 'true_false', 'short_answer']

    # Generated content
    questions = Column(JSON, nullable=False)
    """
    questions format:
    [
        {
            "question": "What is...",
            "type": "mcq",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "...",
            "difficulty": "medium",
            "bloom_level": "understand"
        }
    ]
    """

    # Quality metrics
    quality_score = Column(Float)  # 0-100, based on review
    instructor_rating = Column(Integer)  # 1-5
    used_in_course = Column(Boolean, default=False)
    review_notes = Column(Text)

    # AI metadata
    model_used = Column(String(50), default="gpt-4")
    generation_cost = Column(Float)  # in USD
    generation_time = Column(Float)  # in seconds

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ContentDifficultyAnalysis(Base):
    """
    Store difficulty analysis results for course content.
    """

    __tablename__ = "content_difficulty_analyses"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # 'course', 'lesson'

    # Readability scores
    flesch_reading_ease = Column(Float)  # 0-100
    flesch_kincaid_grade = Column(Float)  # Grade level
    gunning_fog_index = Column(Float)
    smog_index = Column(Float)

    # Complexity metrics
    avg_sentence_length = Column(Float)
    avg_word_length = Column(Float)
    vocabulary_complexity = Column(Float)  # 0-100
    concept_density = Column(Float)  # 0-100

    # Analysis results
    recommended_level = Column(String(50))  # 'beginner', 'intermediate', 'advanced'
    target_audience = Column(String(100))
    estimated_reading_time = Column(Integer)  # in minutes

    # Suggestions
    simplification_suggestions = Column(JSON)
    difficult_terms = Column(JSON)  # List of complex terms

    # Metadata
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIUsageLog(Base):
    """
    Track AI API usage for cost monitoring and analytics.
    """

    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature = Column(
        String(50), nullable=False, index=True
    )  # 'essay_grading', 'quiz_gen', etc.

    # API details
    model_used = Column(
        String(50), nullable=False
    )  # 'gpt-4', 'gpt-3.5-turbo', 'text-embedding-ada-002'
    tokens_used = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)  # in USD

    # Request details
    request_data = Column(JSON)  # Sanitized request params
    response_time = Column(Float)  # in milliseconds
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
