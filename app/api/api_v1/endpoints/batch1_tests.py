from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.api.deps import get_current_active_user
from app.db.session import SessionLocal
from app.models.user import User
from app.models.batch1 import Batch1TestResult
from pydantic import BaseModel

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestAnswer(BaseModel):
    qId: int
    answer: int
    isCorrect: bool
    confidence: Optional[int] = None  # 1=100% Sure, 2=50-50, 3=One Known, 4=Blind Guess

class TestResultCreate(BaseModel):
    cycle_id: int
    day_number: int
    score: float
    total_questions: int
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    answers: List[TestAnswer]

class TestResultResponse(BaseModel):
    id: int
    cycle_id: int
    day_number: int
    score: float
    total_questions: int
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    timestamp: datetime

    class Config:
        from_attributes = True

@router.post("/test-results", response_model=Dict[str, Any])
async def save_test_result(
    result_data: TestResultCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a student's MCQ test result"""
    try:
        db_result = Batch1TestResult(
            user_id=current_user.id,
            cycle_id=result_data.cycle_id,
            day_number=result_data.day_number,
            score=result_data.score,
            total_questions=result_data.total_questions,
            correct_count=result_data.correct_count,
            incorrect_count=result_data.incorrect_count,
            unanswered_count=result_data.unanswered_count,
            answers_json=json.dumps([a.dict() for a in result_data.answers])
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return {"success": True, "id": db_result.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-results", response_model=List[TestResultResponse])
async def get_test_results(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all test results for the current student"""
    results = db.query(Batch1TestResult).filter(
        Batch1TestResult.user_id == current_user.id
    ).order_by(Batch1TestResult.timestamp.desc()).all()
    return results

@router.get("/test-results/{result_id}")
async def get_test_result_detail(
    result_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis for a specific test result"""
    result = db.query(Batch1TestResult).filter(
        Batch1TestResult.id == result_id,
        Batch1TestResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "id": result.id,
        "cycle_id": result.cycle_id,
        "day_number": result.day_number,
        "score": result.score,
        "total_questions": result.total_questions,
        "correct_count": result.correct_count,
        "incorrect_count": result.incorrect_count,
        "unanswered_count": result.unanswered_count,
        "answers": json.loads(result.answers_json) if result.answers_json else [],
        "timestamp": result.timestamp
    }
