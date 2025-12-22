from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Text,
    Float,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    MATCHING = "matching"
    ORDERING = "ordering"
    FILL_IN_BLANK = "fill_in_blank"  # New: Fill in the blank questions
    CODE_EXECUTION = "code_execution"  # New: Code execution with test cases
    ESSAY = "essay"  # New: Essay questions with AI grading


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lesson_id = Column(
        Integer, ForeignKey("lessons.id"), nullable=True
    )  # Optional link to a specific lesson

    # Basic Settings
    time_limit_minutes = Column(Integer, nullable=True)  # None means no limit
    passing_score = Column(Float, default=70.0)
    max_attempts = Column(Integer, nullable=True)  # None means unlimited
    is_published = Column(Boolean, default=False)
    shuffle_questions = Column(Boolean, default=False)
    show_correct_answers = Column(Boolean, default=True)

    # NEW: Interactive Features
    instant_feedback = Column(Boolean, default=True)  # Show feedback after each answer
    show_score_immediately = Column(Boolean, default=True)  # Show score when completed
    randomize_options = Column(Boolean, default=False)  # Randomize answer options
    allow_review_answers = Column(
        Boolean, default=True
    )  # Allow reviewing after completion
    show_hints = Column(Boolean, default=False)  # Show hints for questions
    require_all_questions = Column(Boolean, default=True)  # Must answer all questions
    allow_backtrack = Column(Boolean, default=True)  # Can go back to previous questions

    # NEW: Auto-grading Settings
    enable_ai_grading = Column(Boolean, default=False)  # Enable AI grading for essays
    ai_grading_model = Column(
        String, nullable=True, default="gemini"
    )  # AI model to use
    manual_review_threshold = Column(
        Float, default=0.7
    )  # Confidence threshold for manual review

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", backref="quizzes")
    lesson = relationship("Lesson", backref="quiz")
    questions = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    text = Column(Text, nullable=False)
    type = Column(
        String, nullable=False
    )  # stored as string, validated against QuestionType
    points = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)  # Explanation for the correct answer

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order_index",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    # For matching questions (left side is text, right side is match_text)
    match_text = Column(Text, nullable=True)

    # Relationships
    question = relationship("Question", back_populates="options")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    score = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
    answers = relationship(
        "StudentAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    # For MCQs/TrueFalse, store option_id(s)
    selected_option_id = Column(
        Integer, ForeignKey("question_options.id"), nullable=True
    )

    # For Short/Long Answer, store text
    text_response = Column(Text, nullable=True)

    is_correct = Column(Boolean, default=False)
    points_awarded = Column(Float, default=0.0)

    # NEW: Time tracking
    time_spent_seconds = Column(Integer, default=0)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")


# NEW MODEL: Quiz Feedback
class QuizFeedback(Base):
    """Detailed feedback for quiz questions"""

    __tablename__ = "quiz_feedback"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    # General feedback
    feedback_text = Column(Text, nullable=True)  # General feedback shown always

    # Specific feedback based on answer
    feedback_for_correct = Column(Text, nullable=True)  # Shown when answer is correct
    feedback_for_incorrect = Column(Text, nullable=True)  # Shown when answer is wrong

    # Hints and additional resources
    hint_text = Column(Text, nullable=True)  # Hint for struggling students
    explanation_url = Column(String, nullable=True)  # Link to explanation video/article
    media_url = Column(String, nullable=True)  # Additional media (image, video)

    # Relationships
    question = relationship("Question", backref="feedback")


# NEW MODEL: Quiz Attempt Analytics
class QuizAttemptAnalytics(Base):
    """Detailed analytics for each quiz attempt"""

    __tablename__ = "quiz_attempt_analytics"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), unique=True)

    # Time metrics
    time_spent_seconds = Column(Integer, default=0)
    average_time_per_question = Column(Float, default=0.0)

    # Question metrics
    questions_answered = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    questions_incorrect = Column(Integer, default=0)
    questions_skipped = Column(Integer, default=0)
    questions_reviewed = Column(Integer, default=0)  # How many times reviewed answers

    # Performance metrics
    difficulty_rating = Column(Float, nullable=True)  # Student's difficulty rating
    confidence_score = Column(Float, default=0.0)  # How confident student felt (0-1)

    # Behavior tracking
    times_backtracked = Column(Integer, default=0)  # How many times went back
    hints_used = Column(Integer, default=0)  # How many hints used

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    attempt = relationship("QuizAttempt", backref="analytics", uselist=False)


# NEW MODEL: Assessment Rubric
class AssessmentRubric(Base):
    """Rubrics for grading essay and long-form questions"""

    __tablename__ = "assessment_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    # Rubric details
    criteria_name = Column(String, nullable=False)  # e.g., "Content Quality", "Grammar"
    max_points = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    # Rubric levels stored as JSON
    # Example: [{"score": 4, "label": "Excellent", "description": "..."}, ...]
    levels = Column(Text, nullable=True)  #  JSON string

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    question = relationship("Question", backref="rubrics")


# NEW MODEL: AI Grading Result
class AIGradingResult(Base):
    """Results from AI-powered automated grading"""

    __tablename__ = "ai_grading_results"

    id = Column(Integer, primary_key=True, index=True)
    student_answer_id = Column(Integer, ForeignKey("student_answers.id"), unique=True)

    # AI grading results
    ai_score = Column(Float, default=0.0)  # Score given by AI
    ai_feedback = Column(Text, nullable=True)  # Feedback from AI
    confidence = Column(Float, default=0.0)  # AI's confidence (0-1)

    # Rubric-based scoring (stored as JSON)
    # Example: {"Content": 8, "Grammar": 9, "Structure": 7}
    rubric_scores = Column(Text, nullable=True)  # JSON string

    # Moderation
    needs_manual_review = Column(Boolean, default=False)  # Flag for instructor review
    instructor_override_score = Column(Float, nullable=True)  # Instructor's final score
    instructor_feedback = Column(
        Text, nullable=True
    )  # Instructor's additional feedback
    reviewed_by_instructor = Column(Boolean, default=False)

    # metadata
    model_used = Column(String, default="gemini")  # Which AI model was used
    grading_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student_answer = relationship("StudentAnswer", backref="ai_grading", uselist=False)
