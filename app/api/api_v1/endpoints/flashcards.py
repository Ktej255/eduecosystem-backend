from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.services.flashcard_service import flashcard_service
from pydantic import BaseModel

router = APIRouter()

class ReviewUpdate(BaseModel):
    card_id: int
    grade: int # 1-4

@router.get("/lesson/{lesson_id}")
async def get_lesson_flashcards(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Fetch (and generate if needed) flashcards for a specific lesson.
    """
    # For now, we only generate via segment_key for Batch 1.
    # We might need to map lesson_id to segment_key if applicable.
    cards = flashcard_service.get_user_cards_due(db, current_user.id, lesson_id=lesson_id)
    return cards

@router.get("/batch1/{segment_key}")
async def get_batch1_flashcards(
    segment_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Fetch/Generate flashcards for a Batch 1 video segment.
    """
    # Trigger generation if not exists
    await flashcard_service.generate_cards_from_video(db, segment_key)
    
    # Get due cards
    cards = flashcard_service.get_user_cards_due(db, current_user.id)
    # Filter by segment key if needed (the service currently filters by lesson_id)
    # Let's adjust the query specifically for segment_key if needed or rely on the service returning all due.
    # For now, let's filter the results in memory if the service doesn't support segment_key filtering yet.
    
    return [c for c in cards if c.get("id") in [rc.id for rc in db.query(Flashcard).filter(Flashcard.batch1_segment_key == segment_key).all()]]

@router.post("/review")
async def review_flashcard(
    review: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Update a flashcard's progress after a review.
    """
    progress = flashcard_service.update_progress(db, current_user.id, review.card_id, review.grade)
    return {
        "status": "success",
        "next_due": progress.next_due_date,
        "new_stability": progress.stability
    }
