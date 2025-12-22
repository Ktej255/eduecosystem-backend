"""
AI Tools API Endpoints

API endpoints for AI-powered features: grading, quiz generation, difficulty analysis, plagiarism detection.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict

from app.api import deps
from app.models.user import User
from app.services.ai_grading_service import AIGradingService
from app.services.quiz_generator_service import QuizGeneratorService
from app.services.difficulty_analyzer_service import DifficultyAnalyzerService
from app.services.plagiarism_service import PlagiarismService

router = APIRouter()

# --- Request/Response Schemas ---


class EssayGradeRequest(BaseModel):
    submission_id: int
    essay_text: str
    rubric: Dict
    max_score: int = 100


class EssayGradeResponse(BaseModel):
    submission_id: int
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]
    grammar_score: int
    originality_score: int

    model_config = ConfigDict(from_attributes=True)


class QuizGenerationRequest(BaseModel):
    course_id: int
    lesson_id: Optional[int] = None
    content: str
    num_questions: int = 10
    difficulty: str = "medium"
    question_types: List[str] = ["mcq", "true_false"]


class QuizGenerationResponse(BaseModel):
    id: int
    questions: List[Dict]
    generation_time: float
    estimated_cost: float


class DifficultyAnalysisRequest(BaseModel):
    content_id: int
    content_type: str
    content_text: str
    target_level: str = "undergraduate"


class DifficultyAnalysisResponse(BaseModel):
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    recommended_level: str
    target_audience: str
    estimated_reading_time: int
    simplification_suggestions: List[str]

    model_config = ConfigDict(from_attributes=True)


class PlagiarismCheckRequest(BaseModel):
    submission_id: int
    text: str
    assignment_id: int
    threshold: float = 25.0


class PlagiarismCheckResponse(BaseModel):
    submission_id: int
    similarity_percentage: float
    originality_score: float
    matches: List[Dict]
    is_plagiarized: bool
    review_required: bool

    model_config = ConfigDict(from_attributes=True)


# --- AI Grading Endpoints ---


@router.post("/grade-essay", response_model=EssayGradeResponse)
async def grade_essay(
    request: EssayGradeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Grade an essay using AI.
    """
    try:
        result = await AIGradingService.grade_essay(
            db=db,
            submission_id=request.submission_id,
            essay_text=request.essay_text,
            rubric=request.rubric,
            max_score=request.max_score,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")


@router.get("/grading-result/{submission_id}", response_model=EssayGradeResponse)
def get_grading_result(
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get AI grading result for a submission.
    """
    result = AIGradingService.get_grading_result(db, submission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Grading result not found")
    return result


# --- Quiz Generation Endpoints ---


@router.post("/generate-quiz", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate a quiz from course content using AI.
    """
    try:
        quiz = await QuizGeneratorService.generate_quiz(
            db=db,
            course_id=request.course_id,
            lesson_id=request.lesson_id,
            content=request.content,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types,
            user_id=current_user.id,
        )
        return {
            "id": quiz.id,
            "questions": quiz.questions,
            "generation_time": quiz.generation_time,
            "estimated_cost": quiz.generation_cost,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.get("/generated-quiz/{quiz_id}")
def get_generated_quiz(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a generated quiz by ID.
    """
    quiz = QuizGeneratorService.get_generated_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.post("/rate-quiz/{quiz_id}")
def rate_quiz(
    quiz_id: int,
    rating: int,
    notes: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Rate the quality of a generated quiz (instructor feedback).
    """
    QuizGeneratorService.rate_quiz(db, quiz_id, rating, notes)
    return {"message": "Quiz rated successfully"}


# --- Difficulty Analysis Endpoints ---


@router.post("/analyze-difficulty", response_model=DifficultyAnalysisResponse)
def analyze_difficulty(
    request: DifficultyAnalysisRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Analyze content difficulty and readability.
    """
    try:
        analysis = DifficultyAnalyzerService.analyze_difficulty(
            db=db,
            content_id=request.content_id,
            content_type=request.content_type,
            content_text=request.content_text,
            target_level=request.target_level,
            user_id=current_user.id,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# --- Plagiarism Detection Endpoints ---


@router.post("/check-plagiarism", response_model=PlagiarismCheckResponse)
async def check_plagiarism(
    request: PlagiarismCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Check submission for plagiarism.
    """
    try:
        check = await PlagiarismService.check_plagiarism(
            db=db,
            submission_id=request.submission_id,
            text=request.text,
            assignment_id=request.assignment_id,
            student_id=current_user.id,
            threshold=request.threshold,
            user_id=current_user.id,
        )
        return check
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Plagiarism check failed: {str(e)}"
        )


@router.get(
    "/plagiarism-result/{submission_id}", response_model=PlagiarismCheckResponse
)
def get_plagiarism_result(
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get plagiarism check result for a submission.
    """
    check = PlagiarismService.get_plagiarism_check(db, submission_id)
    if not check:
        raise HTTPException(status_code=404, detail="Plagiarism check not found")
    return check


@router.post("/plagiarism-review/{check_id}")
def review_plagiarism(
    check_id: int,
    notes: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Mark plagiarism check as reviewed (instructor only).
    """
    PlagiarismService.review_plagiarism_check(db, check_id, notes)
    return {"message": "Review recorded"}


# --- Usage Analytics ---


@router.get("/usage-stats")
def get_ai_usage_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get AI usage statistics for the current user.
    """
    from app.models.ai_features import AIUsageLog
    from sqlalchemy import func

    stats = (
        db.query(
            AIUsageLog.feature,
            func.count(AIUsageLog.id).label("count"),
            func.sum(AIUsageLog.tokens_used).label("total_tokens"),
            func.sum(AIUsageLog.estimated_cost).label("total_cost"),
        )
        .filter(AIUsageLog.user_id == current_user.id)
        .group_by(AIUsageLog.feature)
        .all()
    )

    return [
        {
            "feature": s.feature,
            "usage_count": s.count,
            "total_tokens": s.total_tokens,
            "total_cost": float(s.total_cost) if s.total_cost else 0,
        }
        for s in stats
    ]
