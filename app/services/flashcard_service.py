import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.flashcard import Flashcard, FlashcardProgress
from app.services.transcription_service import get_video_document
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class FlashcardService:
    """
    Handles Flashcard generation via AI and Spaced Repetition (FSRS) logic.
    """

    @staticmethod
    async def generate_cards_from_video(db: Session, segment_key: str, lesson_id: Optional[int] = None) -> List[Flashcard]:
        """
        Generates flashcards from a video transcript using AI.
        """
        # Check if cards already exist to avoid duplicates
        existing_cards = db.query(Flashcard).filter(Flashcard.batch1_segment_key == segment_key).all()
        if existing_cards:
            return existing_cards

        # Get transcription document
        doc = get_video_document(segment_key)
        if not doc or "key_points_for_recall" not in doc:
            logger.warning(f"No transcription document found for {segment_key}")
            return []

        content_for_ai = json.dumps({
            "title": doc.get("title"),
            "summary": doc.get("summary"),
            "key_points": doc.get("key_points_for_recall"),
            "definitions": doc.get("definitions")
        })

        system_prompt = """
        You are an expert educator. Create 5-8 high-quality flashcards (Question/Answer pairs) from the provided video content.
        Focus on key concepts, facts, and definitions.
        Return ONLY a JSON array of objects with "question", "answer", and "explanation" fields.
        """

        prompt = f"Video Content:\n{content_for_ai}\n\nGenerate flashcards now:"

        try:
            response_text = gemini_service.generate_text(
                prompt=f"{system_prompt}\n\n{prompt}",
                is_complex=True
            )
            
            # Extract JSON
            import re
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                logger.error("Failed to extract JSON from AI response")
                return []
            
            cards_data = json.loads(json_match.group())
            
            new_cards = []
            for data in cards_data:
                card = Flashcard(
                    lesson_id=lesson_id,
                    batch1_segment_key=segment_key,
                    question=data["question"],
                    answer=data["answer"],
                    explanation=data.get("explanation"),
                    source_type="ai_generated"
                )
                db.add(card)
                new_cards.append(card)
            
            db.commit()
            return new_cards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            return []

    @staticmethod
    def get_user_cards_due(db: Session, user_id: int, lesson_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns cards due for review for a user.
        """
        now = datetime.now(timezone.utc)
        
        # Query for due cards or new cards
        query = db.query(Flashcard, FlashcardProgress).outerjoin(
            FlashcardProgress, 
            (FlashcardProgress.flashcard_id == Flashcard.id) & (FlashcardProgress.user_id == user_id)
        )
        
        if lesson_id:
            query = query.filter(Flashcard.lesson_id == lesson_id)
            
        cards = query.all()
        
        result = []
        for card, progress in cards:
            is_due = False
            if not progress:
                is_due = True # New card
            elif progress.next_due_date and progress.next_due_date <= now:
                is_due = True
                
            if is_due:
                result.append({
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "explanation": card.explanation,
                    "progress": {
                        "stability": progress.stability if progress else 1.0,
                        "difficulty": progress.difficulty if progress else 5.0,
                        "status": progress.status if progress else "new"
                    } if progress else None
                })
        
        return result

    @staticmethod
    def update_progress(db: Session, user_id: int, card_id: int, grade: int):
        """
        Updates card progress based on FSRS grade (1-4).
        1: Again (Forgot), 2: Hard, 3: Good, 4: Easy
        """
        progress = db.query(FlashcardProgress).filter(
            FlashcardProgress.user_id == user_id,
            FlashcardProgress.flashcard_id == card_id
        ).first()

        if not progress:
            progress = FlashcardProgress(user_id=user_id, flashcard_id=card_id)
            db.add(progress)

        # Basic FSRS-like update logic
        # S_new = S_old * factor(grade)
        factors = {1: 0.25, 2: 1.2, 3: 1.5, 4: 2.2}
        
        progress.stability = progress.stability * factors.get(grade, 1.0)
        
        # Update difficulty
        # More difficult if grade is low
        if grade < 3:
            progress.difficulty = min(10.0, progress.difficulty + 0.5)
        else:
            progress.difficulty = max(1.0, progress.difficulty - 0.2)

        progress.last_review_date = datetime.now(timezone.utc)
        progress.next_due_date = progress.last_review_date + timedelta(days=progress.stability)
        progress.reps += 1
        if grade == 1:
            progress.lapses += 1
            progress.status = "learning"
        elif progress.stability > 21:
            progress.status = "mastered"
        else:
            progress.status = "reviewing"

        db.commit()
        return progress

flashcard_service = FlashcardService()
