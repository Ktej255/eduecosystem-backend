from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.api import deps
from app.models.user import User
from app.models.quiz import (
    Question,
    QuizFeedback,
    AssessmentRubric,
    AIGradingResult,
    StudentAnswer,
)
from app.schemas.quiz import (
    QuizFeedbackCreate,
    QuizFeedbackUpdate,
    QuizFeedback as QuizFeedbackSchema,
    AssessmentRubricCreate,
    AssessmentRubricUpdate,
    AssessmentRubric as AssessmentRubricSchema,
    AIGradingResultUpdate,
    AIGradingResult as AIGradingResultSchema,
)

router = APIRouter()

# ============================================================================
# QUIZ FEEDBACK ENDPOINTS
# ============================================================================


@router.post(
    "/", response_model=QuizFeedbackSchema, status_code=status.HTTP_201_CREATED
)
def create_quiz_feedback(
    *,
    db: Session = Depends(deps.get_db),
    feedback_in: QuizFeedbackCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create feedback for a quiz question (instructor only).
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Verify question exists
    question = db.query(Question).filter(Question.id == feedback_in.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if feedback already exists
    existing = (
        db.query(QuizFeedback)
        .filter(QuizFeedback.question_id == feedback_in.question_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Feedback already exists for this question. Use UPDATE instead.",
        )

    # Create feedback
    db_feedback = QuizFeedback(
        question_id=feedback_in.question_id,
        feedback_text=feedback_in.feedback_text,
        feedback_for_correct=feedback_in.feedback_for_correct,
        feedback_for_incorrect=feedback_in.feedback_for_incorrect,
        hint_text=feedback_in.hint_text,
        explanation_url=feedback_in.explanation_url,
        media_url=feedback_in.media_url,
    )

    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_feedback


@router.get("/{feedback_id}", response_model=QuizFeedbackSchema)
def get_quiz_feedback(
    feedback_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get feedback by ID"""
    feedback = db.query(QuizFeedback).filter(QuizFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.get("/question/{question_id}", response_model=QuizFeedbackSchema)
def get_feedback_for_question(
    question_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get feedback for a specific question"""
    feedback = (
        db.query(QuizFeedback).filter(QuizFeedback.question_id == question_id).first()
    )

    if not feedback:
        raise HTTPException(
            status_code=404, detail="No feedback found for this question"
        )

    return feedback


@router.put("/{feedback_id}", response_model=QuizFeedbackSchema)
def update_quiz_feedback(
    feedback_id: int,
    *,
    db: Session = Depends(deps.get_db),
    feedback_in: QuizFeedbackUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update quiz feedback (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    feedback = db.query(QuizFeedback).filter(QuizFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Update fields
    update_data = feedback_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback, field, value)

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


@router.delete(
    "/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
def delete_quiz_feedback(
    feedback_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete quiz feedback (instructor only)"""
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    feedback = db.query(QuizFeedback).filter(QuizFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db.delete(feedback)
    db.commit()

    return None


# ============================================================================
# ASSESSMENT RUBRIC ENDPOINTS
# ============================================================================


@router.post(
    "/rubrics",
    response_model=AssessmentRubricSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_rubric(
    *,
    db: Session = Depends(deps.get_db),
    rubric_in: AssessmentRubricCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a grading rubric for a question (instructor only).
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Verify question exists
    question = db.query(Question).filter(Question.id == rubric_in.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Convert levels list to JSON string
    levels_json = (
        json.dumps([level.dict() for level in rubric_in.levels])
        if rubric_in.levels
        else None
    )

    # Create rubric
    db_rubric = AssessmentRubric(
        question_id=rubric_in.question_id,
        criteria_name=rubric_in.criteria_name,
        max_points=rubric_in.max_points,
        description=rubric_in.description,
        order_index=rubric_in.order_index,
        levels=levels_json,
    )

    db.add(db_rubric)
    db.commit()
    db.refresh(db_rubric)

    return db_rubric


@router.get("/rubrics/{rubric_id}", response_model=AssessmentRubricSchema)
def get_rubric(
    rubric_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get rubric by ID"""
    rubric = db.query(AssessmentRubric).filter(AssessmentRubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # Parse JSON levels
    if rubric.levels:
        rubric.levels = json.loads(rubric.levels)

    return rubric


@router.get(
    "/rubrics/question/{question_id}", response_model=List[AssessmentRubricSchema]
)
def get_rubrics_for_question(
    question_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all rubrics for a specific question"""
    rubrics = (
        db.query(AssessmentRubric)
        .filter(AssessmentRubric.question_id == question_id)
        .order_by(AssessmentRubric.order_index)
        .all()
    )

    # Parse JSON levels for each rubric
    for rubric in rubrics:
        if rubric.levels:
            rubric.levels = json.loads(rubric.levels)

    return rubrics


@router.put("/rubrics/{rubric_id}", response_model=AssessmentRubricSchema)
def update_rubric(
    rubric_id: int,
    *,
    db: Session = Depends(deps.get_db),
    rubric_in: AssessmentRubricUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update rubric (instructor only)"""
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    rubric = db.query(AssessmentRubric).filter(AssessmentRubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # Update fields
    update_data = rubric_in.dict(exclude_unset=True)

    # Convert levels to JSON if provided
    if "levels" in update_data and update_data["levels"]:
        update_data["levels"] = json.dumps(
            [
                level.dict() if hasattr(level, "dict") else level
                for level in update_data["levels"]
            ]
        )

    for field, value in update_data.items():
        setattr(rubric, field, value)

    db.add(rubric)
    db.commit()
    db.refresh(rubric)

    # Parse JSON for response
    if rubric.levels:
        rubric.levels = json.loads(rubric.levels)

    return rubric


@router.delete(
    "/rubrics/{rubric_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
def delete_rubric(
    rubric_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete rubric (instructor only)"""
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    rubric = db.query(AssessmentRubric).filter(AssessmentRubric.id == rubric_id).first()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    db.delete(rubric)
    db.commit()

    return None


# ============================================================================
# AI GRADING ENDPOINTS
# ============================================================================


@router.get("/ai-grading/review-queue", response_model=List[AIGradingResultSchema])
def get_review_queue(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get queue of AI-graded submissions needing manual review (instructor only).
    Returns submissions with low confidence scores.
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    results = (
        db.query(AIGradingResult)
        .filter(
            AIGradingResult.needs_manual_review == True,
            AIGradingResult.reviewed_by_instructor == False,
        )
        .order_by(AIGradingResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return results


@router.get("/ai-grading/{result_id}", response_model=AIGradingResultSchema)
def get_ai_grading_result(
    result_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get AI grading result by ID"""
    result = db.query(AIGradingResult).filter(AIGradingResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="AI grading result not found")

    # Parse JSON rubric scores
    if result.rubric_scores:
        result.rubric_scores = json.loads(result.rubric_scores)

    return result


@router.get("/ai-grading/answer/{answer_id}", response_model=AIGradingResultSchema)
def get_ai_grading_for_answer(
    answer_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get AI grading result for a specific student answer"""
    result = (
        db.query(AIGradingResult)
        .filter(AIGradingResult.student_answer_id == answer_id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404, detail="No AI grading found for this answer"
        )

    # Verify access (student can only see their own, instructor can see all)
    answer = db.query(StudentAnswer).filter(StudentAnswer.id == answer_id).first()
    if answer and answer.attempt.user_id != current_user.id:
        if current_user.role != "instructor" and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized")

    # Parse JSON rubric scores
    if result.rubric_scores:
        result.rubric_scores = json.loads(result.rubric_scores)

    return result


@router.post("/ai-grading/{result_id}/override", response_model=AIGradingResultSchema)
def override_ai_grading(
    result_id: int,
    *,
    db: Session = Depends(deps.get_db),
    override_data: AIGradingResultUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Instructor overrides AI grading with manual score/feedback.
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = db.query(AIGradingResult).filter(AIGradingResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="AI grading result not found")

    # Update with instructor override
    if override_data.instructor_override_score is not None:
        result.instructor_override_score = override_data.instructor_override_score

        # Also update the student answer's points
        answer = result.student_answer
        if answer:
            answer.points_awarded = override_data.instructor_override_score
            db.add(answer)

    if override_data.instructor_feedback:
        result.instructor_feedback = override_data.instructor_feedback

    result.reviewed_by_instructor = True
    result.needs_manual_review = False

    db.add(result)
    db.commit()
    db.refresh(result)

    # Parse JSON rubric scores
    if result.rubric_scores:
        result.rubric_scores = json.loads(result.rubric_scores)

    return result


@router.post("/ai-grading/trigger/{answer_id}", response_model=AIGradingResultSchema)
def trigger_ai_grading_manually(
    answer_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually trigger AI grading for an answer (instructor only).
    Useful for re-grading or grading answers that were skipped.
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    answer = db.query(StudentAnswer).filter(StudentAnswer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Student answer not found")

    # TODO: Implement actual AI grading logic
    # For now, return placeholder
    raise HTTPException(
        status_code=501,
        detail="AI grading service not yet implemented. Coming in Phase 4.",
    )
