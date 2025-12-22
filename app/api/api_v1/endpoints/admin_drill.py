"""
Admin API endpoints for Drill Question Management
CRUD operations for questions, content, and model answers
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.drill import DrillQuestion, DrillContent, DrillModelAnswer
from app.schemas.drill import (
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionComplete,
    ContentCreate, ContentUpdate, ContentResponse,
    ModelAnswerCreate, ModelAnswerUpdate, ModelAnswerResponse,
    BulkQuestionUpload, BulkUploadResponse
)

router = APIRouter()


def check_admin(current_user: User = Depends(get_current_user)):
    """Verify user is admin"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== QUESTION CRUD ====================

@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Create a new drill question"""
    db_question = DrillQuestion(
        **question.dict(),
        created_by=current_user.id
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.get("/questions", response_model=List[QuestionResponse])
async def list_questions(
    gs_paper: Optional[str] = Query(None, pattern="^GS[1-4]$"),
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """List all questions with optional filters"""
    query = db.query(DrillQuestion)
    
    if gs_paper:
        query = query.filter(DrillQuestion.gs_paper == gs_paper)
    if topic:
        query = query.filter(DrillQuestion.topic.ilike(f"%{topic}%"))
    if difficulty:
        query = query.filter(DrillQuestion.difficulty == difficulty)
    
    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/questions/{question_id}", response_model=QuestionComplete)
async def get_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get a single question with content and model answer"""
    question = db.query(DrillQuestion).filter(DrillQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {
        "question": question,
        "content": question.content,
        "model_answer": question.model_answer
    }


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Update a question"""
    db_question = db.query(DrillQuestion).filter(DrillQuestion.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_question, field, value)
    
    db.commit()
    db.refresh(db_question)
    return db_question


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Delete a question"""
    db_question = db.query(DrillQuestion).filter(DrillQuestion.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(db_question)
    db.commit()
    return {"success": True, "message": "Question deleted"}


# ==================== CONTENT CRUD ====================

@router.post("/content", response_model=ContentResponse)
async def create_content(
    content: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Create content for a question"""
    # Check if question exists
    question = db.query(DrillQuestion).filter(DrillQuestion.id == content.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if content already exists
    existing = db.query(DrillContent).filter(DrillContent.question_id == content.question_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Content already exists for this question")
    
    db_content = DrillContent(**content.dict())
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: UUID,
    content_update: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Update content"""
    db_content = db.query(DrillContent).filter(DrillContent.id == content_id).first()
    if not db_content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    update_data = content_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_content, field, value)
    
    db.commit()
    db.refresh(db_content)
    return db_content


# ==================== MODEL ANSWER CRUD ====================

@router.post("/model-answers", response_model=ModelAnswerResponse)
async def create_model_answer(
    model_answer: ModelAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Create model answer for a question"""
    # Check if question exists
    question = db.query(DrillQuestion).filter(DrillQuestion.id == model_answer.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check if model answer already exists
    existing = db.query(DrillModelAnswer).filter(
        DrillModelAnswer.question_id == model_answer.question_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Model answer already exists for this question")
    
    # Calculate word count if not provided
    data = model_answer.dict()
    if not data.get('word_count'):
        data['word_count'] = len(data['answer_text'].split())
    
    db_model_answer = DrillModelAnswer(**data)
    db.add(db_model_answer)
    db.commit()
    db.refresh(db_model_answer)
    return db_model_answer


@router.put("/model-answers/{answer_id}", response_model=ModelAnswerResponse)
async def update_model_answer(
    answer_id: UUID,
    answer_update: ModelAnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Update model answer"""
    db_answer = db.query(DrillModelAnswer).filter(DrillModelAnswer.id == answer_id).first()
    if not db_answer:
        raise HTTPException(status_code=404, detail="Model answer not found")
    
    update_data = answer_update.dict(exclude_unset=True)
    
    # Recalculate word count if answer text is updated
    if 'answer_text' in update_data:
        update_data['word_count'] = len(update_data['answer_text'].split())
    
    for field, value in update_data.items():
        setattr(db_answer, field, value)
    
    db.commit()
    db.refresh(db_answer)
    return db_answer


# ==================== BULK UPLOAD ====================

@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_questions(
    upload: BulkQuestionUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Bulk upload questions"""
    total = len(upload.questions)
    successful = 0
    failed = 0
    errors = []
    
    for idx, question_data in enumerate(upload.questions):
        try:
            db_question = DrillQuestion(
                **question_data.dict(),
                created_by=current_user.id
            )
            db.add(db_question)
            db.commit()
            successful += 1
        except Exception as e:
            failed += 1
            errors.append({
                "index": idx,
                "question": question_data.question_text[:50] + "...",
                "error": str(e)
            })
            db.rollback()
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "errors": errors
    }


# ==================== STATISTICS ====================

@router.get("/questions/stats/summary")
async def get_question_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get question statistics"""
    total_questions = db.query(DrillQuestion).count()
    
    # Count by GS paper
    gs_counts = {}
    for gs in ["GS1", "GS2", "GS3", "GS4"]:
        count = db.query(DrillQuestion).filter(DrillQuestion.gs_paper == gs).count()
        gs_counts[gs] = count
    
    # Count by difficulty
    difficulty_counts = {}
    for diff in ["easy", "medium", "hard"]:
        count = db.query(DrillQuestion).filter(DrillQuestion.difficulty == diff).count()
        difficulty_counts[diff] = count
    
    # Questions with/without content
    with_content = db.query(DrillQuestion).join(DrillContent).count()
    with_model_answer = db.query(DrillQuestion).join(DrillModelAnswer).count()
    
    return {
        "total_questions": total_questions,
        "by_gs_paper": gs_counts,
        "by_difficulty": difficulty_counts,
        "with_content": with_content,
        "with_model_answer": with_model_answer,
        "completion_rate": (with_content / total_questions * 100) if total_questions > 0 else 0
    }
