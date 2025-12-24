"""
AI Grading Service (Refactored 2025)
Uses GeminiService with tiered Pro/Flash logic for grading.
"""

import logging
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.gemini_service import gemini_service
from app.models.ai_features import AIUsageLog
from app.models.quiz import AIGradingResult

logger = logging.getLogger(__name__)

class AIGradingService:
    @staticmethod
    async def grade_essay(
        db: Session,
        submission_id: int,
        essay_text: str,
        rubric: Dict,
        max_score: int = 100,
        current_user: Any = None,
    ) -> AIGradingResult:
        """Grade using tiered Gemini AI"""
        
        prompt = f"""Expert Essay Grader. Max Score: {max_score}. 
Rubric: {rubric}
Essay: {essay_text}

Return JSON with: score, feedback, strengths (list), improvements (list)."""

        try:
            # Call tiered AI (Auto-selects Pro for Premium users)
            response_text = gemini_service.generate_text(
                prompt=prompt,
                user=current_user,
                is_complex=True, # Grading requires high reasoning
                temperature=0.3
            )

            import json
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}

            grading_result = AIGradingResult(
                submission_id=submission_id,
                essay_text=essay_text,
                score=Decimal(str(data.get("score", 0))),
                max_score=Decimal(str(max_score)),
                feedback=data.get("feedback", "No feedback generated"),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                model_used="Gemini 3.0",
                graded_at=datetime.utcnow(),
            )
            db.add(grading_result)
            db.commit()
            return grading_result

        except Exception as e:
            logger.error(f"Grading failed: {e}")
            raise e
