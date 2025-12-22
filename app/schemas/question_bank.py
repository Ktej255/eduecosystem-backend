from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime


# ============================================================================
# QUESTION BANK SCHEMAS
# ============================================================================


class QuestionBankBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    difficulty_level: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    is_active: bool = True


class QuestionBankCreate(QuestionBankBase):
    """Schema for creating a question bank"""

    course_id: int


class QuestionBankUpdate(BaseModel):
    """Schema for updating a question bank"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    is_active: Optional[bool] = None


class QuestionBankInDBBase(QuestionBankBase):
    id: int
    course_id: int
    instructor_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionBank(QuestionBankInDBBase):
    """Full question bank schema"""

    question_count: int = 0
    instructor_name: Optional[str] = None


# ============================================================================
# BANK QUESTION SCHEMAS
# ============================================================================


class BankQuestionBase(BaseModel):
    text: str = Field(..., min_length=1)
    type: str = Field(
        ...,
        pattern="^(multiple_choice|true_false|short_answer|long_answer|matching|ordering)$",
    )
    points: int = Field(default=1, ge=1)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    options: Optional[str] = None  # JSON string
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    tags: Optional[str] = None


class BankQuestionCreate(BankQuestionBase):
    """Schema for creating a bank question"""

    question_bank_ids: List[int] = []  # Add to these banks


class BankQuestionUpdate(BaseModel):
    """Schema for updating a bank question"""

    text: Optional[str] = None
    type: Optional[str] = None
    points: Optional[int] = Field(None, ge=1)
    difficulty: Optional[str] = None
    options: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    tags: Optional[str] = None


class BankQuestionInDBBase(BankQuestionBase):
    id: int
    instructor_id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BankQuestion(BankQuestionInDBBase):
    """Full bank question schema"""

    pass


# ============================================================================
# QUIZ QUESTION POOL SCHEMAS
# ============================================================================


class QuizQuestionPoolBase(BaseModel):
    question_bank_id: int
    num_questions: int = Field(..., ge=1)
    difficulty_filter: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")


class QuizQuestionPoolCreate(QuizQuestionPoolBase):
    """Schema for creating a question pool"""

    quiz_id: int


class QuizQuestionPool(QuizQuestionPoolBase):
    id: int
    quiz_id: int
    created_at: datetime
    question_bank_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# QUIZ GENERATION SCHEMAS
# ============================================================================


class QuizGenerationRequest(BaseModel):
    """Request to generate quiz from question banks"""

    quiz_id: int
    pools: List[QuizQuestionPoolBase]


class QuizGenerationResponse(BaseModel):
    """Response after generating quiz"""

    quiz_id: int
    total_questions_added: int
    questions_by_pool: Dict[int, int]  # bank_id: count
    message: str
