"""
AI Grading Service (Refactored 2025)
Uses GeminiService with tiered Pro/Flash logic for grading.
"""

import logging
from typing import Dict, Optional, Any, List
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime
import json
import re
import time
from app.services.gemini_service import gemini_service
from app.models.ai_features import AIUsageLog
from app.models.quiz import AIGradingResult

logger = logging.getLogger(__name__)

class AIGradingService:
    @staticmethod
    def grade_essay(
        db: Session,
        student_answer_id: int,
        essay_text: str,
        rubric: Dict,
        max_score: float = 100.0,
        current_user: Any = None,
    ) -> AIGradingResult:
        """Grade using tiered Gemini AI"""
        
        prompt = f"""Expert Essay Grader. Max Score: {max_score}. 
Rubric: {json.dumps(rubric)}
Essay: {essay_text}

You must evaluate the essay based strictly on the rubric provided.
Return ONLY a JSON object with the following keys:
- "score" (float): The total score awarded.
- "feedback" (string): Detailed feedback explaining the score.
- "confidence" (float): Your confidence in the grading from 0.0 to 1.0.
- "rubric_scores" (dict): A dictionary mapping each rubric criteria name to the score awarded for that criteria.

Do not include any markdown blocks or additional text. Just the JSON object.
"""

        try:
            start_time = time.time()

            # Call tiered AI (Auto-selects Pro for Premium users)
            response_text = gemini_service.generate_text(
                prompt=prompt,
                user=current_user,
                is_complex=True, # Grading requires high reasoning
                temperature=0.3
            )

            grading_time = time.time() - start_time

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}

            rubric_scores_json = json.dumps(data.get("rubric_scores", {}))

            grading_result = AIGradingResult(
                student_answer_id=student_answer_id,
                ai_score=float(data.get("score", 0.0)),
                ai_feedback=data.get("feedback", "No feedback generated"),
                confidence=float(data.get("confidence", 0.0)),
                rubric_scores=rubric_scores_json,
                needs_manual_review=float(data.get("confidence", 1.0)) < 0.7, # Example threshold
                model_used="gemini",
                grading_time_seconds=grading_time,
            )

            # Check if one already exists
            existing = db.query(AIGradingResult).filter(AIGradingResult.student_answer_id == student_answer_id).first()
            if existing:
                existing.ai_score = grading_result.ai_score
                existing.ai_feedback = grading_result.ai_feedback
                existing.confidence = grading_result.confidence
                existing.rubric_scores = grading_result.rubric_scores
                existing.needs_manual_review = grading_result.needs_manual_review
                existing.model_used = grading_result.model_used
                existing.grading_time_seconds = grading_result.grading_time_seconds
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return existing
            else:
                db.add(grading_result)
                db.commit()
                db.refresh(grading_result)
                return grading_result

        except Exception as e:
            logger.error(f"Grading failed: {e}")
            raise e
