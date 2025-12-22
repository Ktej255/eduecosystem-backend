from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.quiz import QuestionType


# Option Schemas
class QuestionOptionBase(BaseModel):
    text: str
    is_correct: bool = False
    order_index: int = 0
    match_text: Optional[str] = None


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionUpdate(QuestionOptionBase):
    id: Optional[int] = None


class QuestionOption(QuestionOptionBase):
    id: int
    question_id: int

    model_config = ConfigDict(from_attributes=True)


# Question Schemas
class QuestionBase(BaseModel):
    text: str
    type: QuestionType
    points: int = 1
    order_index: int = 0
    explanation: Optional[str] = None


class QuestionCreate(QuestionBase):
    options: List[QuestionOptionCreate] = []


class QuestionUpdate(QuestionBase):
    options: List[QuestionOptionUpdate] = []


class Question(QuestionBase):
    id: int
    quiz_id: int
    options: List[QuestionOption] = []

    model_config = ConfigDict(from_attributes=True)


# Quiz Schemas
class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score: float = 70.0
    max_attempts: Optional[int] = None
    is_published: bool = False
    shuffle_questions: bool = False
    show_correct_answers: bool = True

    # Interactive Features
    instant_feedback: bool = True
    show_score_immediately: bool = True
    randomize_options: bool = False
    allow_review_answers: bool = True
    show_hints: bool = False
    require_all_questions: bool = True
    allow_backtrack: bool = True

    # AI Grading Settings
    enable_ai_grading: bool = False
    ai_grading_model: Optional[str] = "gemini"
    manual_review_threshold: float = 0.7


class QuizCreate(QuizBase):
    course_id: int
    lesson_id: Optional[int] = None
    questions: List[QuestionCreate] = []


class QuizUpdate(QuizBase):
    questions: Optional[List[QuestionUpdate]] = None


class Quiz(QuizBase):
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[Question] = []

    model_config = ConfigDict(from_attributes=True)


# Attempt Schemas
class StudentAnswerCreate(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    text_response: Optional[str] = None
    time_spent_seconds: int = 0  # NEW: Track time per question


class StudentAnswer(StudentAnswerCreate):
    id: int
    is_correct: bool
    points_awarded: float
    submitted_at: Optional[datetime] = None  # NEW

    model_config = ConfigDict(from_attributes=True)


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: List[StudentAnswerCreate] = []


class QuizAttempt(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float
    passed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    answers: List[StudentAnswer] = []

    model_config = ConfigDict(from_attributes=True)


# NEW: Quiz Feedback Schemas
class QuizFeedbackBase(BaseModel):
    feedback_text: Optional[str] = None
    feedback_for_correct: Optional[str] = None
    feedback_for_incorrect: Optional[str] = None
    hint_text: Optional[str] = None
    explanation_url: Optional[str] = None
    media_url: Optional[str] = None


class QuizFeedbackCreate(QuizFeedbackBase):
    question_id: int


class QuizFeedbackUpdate(QuizFeedbackBase):
    pass


class QuizFeedback(QuizFeedbackBase):
    id: int
    question_id: int

    model_config = ConfigDict(from_attributes=True)


# NEW: Quiz Attempt Analytics Schemas
class QuizAttemptAnalyticsBase(BaseModel):
    time_spent_seconds: int = 0
    average_time_per_question: float = 0.0
    questions_answered: int = 0
    questions_correct: int = 0
    questions_incorrect: int = 0
    questions_skipped: int = 0
    questions_reviewed: int = 0
    difficulty_rating: Optional[float] = None
    confidence_score: float = 0.0
    times_backtracked: int = 0
    hints_used: int = 0


class QuizAttemptAnalyticsCreate(QuizAttemptAnalyticsBase):
    attempt_id: int


class QuizAttemptAnalytics(QuizAttemptAnalyticsBase):
    id: int
    attempt_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# NEW: Assessment Rubric Schemas
class RubricLevel(BaseModel):
    """Individual level within a rubric criterion"""

    score: int
    label: str
    description: str


class AssessmentRubricBase(BaseModel):
    criteria_name: str
    max_points: int
    description: Optional[str] = None
    order_index: int = 0
    levels: List[RubricLevel] = []


class AssessmentRubricCreate(AssessmentRubricBase):
    question_id: int


class AssessmentRubricUpdate(AssessmentRubricBase):
    pass


class AssessmentRubric(AssessmentRubricBase):
    id: int
    question_id: int
    created_at: datetime
    # Convert JSON string to dict on output
    levels: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


# NEW: AI Grading Result Schemas
class AIGradingResultBase(BaseModel):
    ai_score: float = 0.0
    ai_feedback: Optional[str] = None
    confidence: float = 0.0
    rubric_scores: Optional[Dict[str, float]] = None
    needs_manual_review: bool = False
    reviewed_by_instructor: bool = False


class AIGradingResultCreate(AIGradingResultBase):
    student_answer_id: int
    model_used: str = "gemini"


class AIGradingResultUpdate(BaseModel):
    instructor_override_score: Optional[float] = None
    instructor_feedback: Optional[str] = None
    reviewed_by_instructor: bool = True


class AIGradingResult(AIGradingResultBase):
    id: int
    student_answer_id: int
    instructor_override_score: Optional[float] = None
    instructor_feedback: Optional[str] = None
    model_used: str
    grading_time_seconds: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# NEW: Enhanced response schemas for interactive quiz taking
class QuestionWithFeedback(Question):
    """Question with feedback information"""

    feedback: Optional[QuizFeedback] = None
    rubrics: List[AssessmentRubric] = []


class StudentAnswerWithFeedback(StudentAnswer):
    """Student answer with feedback and grading info"""

    question: QuestionWithFeedback
    ai_grading: Optional[AIGradingResult] = None


class QuizAttemptWithAnalytics(QuizAttempt):
    """Quiz attempt with full analytics"""

    analytics: Optional[QuizAttemptAnalytics] = None
    answers: List[StudentAnswerWithFeedback] = []


# NEW: Interactive quiz taking schemas
class SubmitAnswerRequest(BaseModel):
    """Request to submit a single answer during quiz"""

    question_id: int
    selected_option_id: Optional[int] = None
    text_response: Optional[str] = None
    time_spent_seconds: int = 0


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer"""

    is_correct: bool
    points_awarded: float
    feedback: Optional[QuizFeedback] = None
    explanation: Optional[str] = None
    show_correct_answer: bool
    correct_option_id: Optional[int] = None


class StartQuizResponse(BaseModel):
    """Response when starting a quiz attempt"""

    attempt_id: int
    quiz: Quiz
    questions: List[QuestionWithFeedback]
    time_limit_minutes: Optional[int] = None
    started_at: datetime


class CompleteQuizRequest(BaseModel):
    """Request to complete a quiz"""

    difficulty_rating: Optional[float] = None
    confidence_score: float = 0.5


class QuizResultsResponse(BaseModel):
    """Detailed quiz results"""

    attempt: QuizAttemptWithAnalytics
    score: float
    passed: bool
    correct_count: int
    incorrect_count: int
    skipped_count: int
    total_questions: int
    percentage: float
    time_spent: int
    feedback_summary: str
