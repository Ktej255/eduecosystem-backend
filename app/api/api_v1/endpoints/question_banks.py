from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import question_bank as crud_qb
from app.crud import permissions as crud_permissions
from app.schemas.question_bank import (
    QuestionBank,
    QuestionBankCreate,
    QuestionBankUpdate,
    BankQuestion,
    BankQuestionCreate,
    BankQuestionUpdate,
    QuizGenerationRequest,
    QuizGenerationResponse,
)

router = APIRouter()


# ============================================================================
# QUESTION BANK ENDPOINTS
# ============================================================================


@router.get("/courses/{course_id}/question-banks", response_model=List[QuestionBank])
def list_question_banks(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
) -> Any:
    """Get all question banks for a course"""
    banks = crud_qb.question_bank.get_by_course(
        db, course_id=course_id, skip=skip, limit=limit
    )

    # Enhance with question counts
    result = []
    for bank in banks:
        bank_dict = QuestionBank.from_orm(bank).model_dump()
        bank_dict["question_count"] = len(bank.questions)
        bank_dict["instructor_name"] = (
            bank.instructor.full_name if bank.instructor else "Unknown"
        )
        result.append(bank_dict)

    return result


@router.get("/", response_model=List[QuestionBank])
def list_all_question_banks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
) -> Any:
    """Get all question banks for the current instructor (across all courses)"""
    if crud.user.is_superuser(current_user):
        banks = crud_qb.question_bank.get_multi(db, skip=skip, limit=limit)
    else:
        # Filter by instructor
        banks = (
            db.query(models.QuestionBank)
            .filter(models.QuestionBank.instructor_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Enhance with question counts
    result = []
    for bank in banks:
        bank_dict = QuestionBank.from_orm(bank).model_dump()
        bank_dict["question_count"] = len(bank.questions)
        bank_dict["instructor_name"] = (
            bank.instructor.full_name if bank.instructor else "Unknown"
        )
        result.append(bank_dict)

    return result


@router.post(
    "/question-banks", response_model=QuestionBank, status_code=status.HTTP_201_CREATED
)
def create_question_bank(
    *,
    db: Session = Depends(deps.get_db),
    bank_in: QuestionBankCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a question bank (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "create_question_bank"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: create_question_bank required",
            )

    bank = crud_qb.question_bank.create_with_instructor(
        db, obj_in=bank_in, instructor_id=current_user.id
    )

    bank_dict = QuestionBank.from_orm(bank).model_dump()
    bank_dict["question_count"] = 0
    bank_dict["instructor_name"] = current_user.full_name

    return bank_dict


@router.put("/question-banks/{bank_id}", response_model=QuestionBank)
def update_question_bank(
    bank_id: int,
    *,
    db: Session = Depends(deps.get_db),
    bank_in: QuestionBankUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a question bank (owner only)"""
    bank = crud_qb.question_bank.get(db, id=bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")

    # Check permission and ownership
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "edit_question_bank"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: edit_question_bank required"
            )
        if bank.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    bank = crud_qb.question_bank.update(db, db_obj=bank, obj_in=bank_in)

    bank_dict = QuestionBank.from_orm(bank).model_dump()
    bank_dict["question_count"] = len(bank.questions)

    return bank_dict


@router.delete("/question-banks/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question_bank(
    bank_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete a question bank (owner only)"""
    bank = crud_qb.question_bank.get(db, id=bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")

    # Check permission and ownership
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "delete_question_bank"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: delete_question_bank required",
            )
        if bank.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    crud_qb.question_bank.remove(db, id=bank_id)


# ============================================================================
# BANK QUESTION ENDPOINTS
# ============================================================================


@router.get("/question-banks/{bank_id}/questions", response_model=List[BankQuestion])
def list_bank_questions(
    bank_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$"),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
) -> Any:
    """Get questions in a question bank"""
    questions = crud_qb.bank_question.get_by_bank(
        db, bank_id=bank_id, difficulty=difficulty, skip=skip, limit=limit
    )
    return questions


@router.post(
    "/bank-questions", response_model=BankQuestion, status_code=status.HTTP_201_CREATED
)
def create_bank_question(
    *,
    db: Session = Depends(deps.get_db),
    question_in: BankQuestionCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a question in question bank (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "edit_question_bank"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: edit_question_bank required"
            )

    question = crud_qb.bank_question.create_with_instructor(
        db, obj_in=question_in, instructor_id=current_user.id
    )
    return question


@router.put("/bank-questions/{question_id}", response_model=BankQuestion)
def update_bank_question(
    question_id: int,
    *,
    db: Session = Depends(deps.get_db),
    question_in: BankQuestionUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a bank question (owner only)"""
    from app.models.question_bank import BankQuestion as BankQuestionModel

    question = (
        db.query(BankQuestionModel).filter(BankQuestionModel.id == question_id).first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check ownership
    if not current_user.is_superuser:
        if question.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    question = crud_qb.bank_question.update(
        db, question_id=question_id, obj_in=question_in
    )
    return question


@router.delete("/bank-questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_question(
    question_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete a bank question (owner only)"""
    from app.models.question_bank import BankQuestion as BankQuestionModel

    question = (
        db.query(BankQuestionModel).filter(BankQuestionModel.id == question_id).first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check ownership
    if not current_user.is_superuser:
        if question.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    crud_qb.bank_question.delete(db, question_id=question_id)


@router.post("/bank-questions/{question_id}/add-to-bank/{bank_id}")
def add_question_to_bank(
    question_id: int,
    bank_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Add a question to a question bank"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "edit_question_bank"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: edit_question_bank required"
            )

    success = crud_qb.bank_question.add_to_bank(
        db, question_id=question_id, bank_id=bank_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Question or bank not found")

    return {"message": "Question added to bank"}


@router.delete("/bank-questions/{question_id}/remove-from-bank/{bank_id}")
def remove_question_from_bank(
    question_id: int,
    bank_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Remove a question from a question bank"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "edit_question_bank"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: edit_question_bank required"
            )

    success = crud_qb.bank_question.remove_from_bank(
        db, question_id=question_id, bank_id=bank_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Question or bank not found")

    return {"message": "Question removed from bank"}


# ============================================================================
# QUIZ GENERATION ENDPOINTS
# ============================================================================


@router.post("/quizzes/generate-from-banks", response_model=QuizGenerationResponse)
def generate_quiz_from_banks(
    *,
    db: Session = Depends(deps.get_db),
    request: QuizGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Generate quiz questions from question banks (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_role(db, current_user.id, "instructor"):
            raise HTTPException(status_code=403, detail="Instructor role required")

    result = crud_qb.quiz_generation.generate_quiz_from_pools(
        db, quiz_id=request.quiz_id, pools=request.pools
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
