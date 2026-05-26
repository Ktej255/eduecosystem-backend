"""
AI Grading Service (Refactored 2025)
Uses GeminiService with tiered Pro/Flash logic for grading.
"""

import logging
import json
import re
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from app.services.gemini_service import gemini_service
from app.models.quiz import AIGradingResult, StudentAnswer, Question, AssessmentRubric

logger = logging.getLogger(__name__)

class AIGradingService:
    @staticmethod
    def grade_quiz_answer(
        db: Session,
        answer_id: int,
        model_name: str,
        threshold: float,
        current_user: Any = None,
    ) -> Optional[AIGradingResult]:
        """Grade a student's answer using tiered Gemini AI."""
        answer = db.query(StudentAnswer).filter(StudentAnswer.id == answer_id).first()
        if not answer or not answer.text_response:
            return None

        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            return None

        # Gather rubrics if any
        rubrics = db.query(AssessmentRubric).filter(AssessmentRubric.question_id == question.id).all()
        rubric_text = ""
        if rubrics:
            rubric_data = [{"criteria": r.criteria_name, "max_points": r.max_points, "description": r.description} for r in rubrics]
            rubric_text = f"Rubrics: {json.dumps(rubric_data)}"
        else:
            rubric_text = f"Max Points: {question.points}"

        prompt = f"""Expert Educational Grader.
You are evaluating a student's answer to the following question.
Question: {question.text}
Student's Answer: {answer.text_response}
{rubric_text}

Return JSON strictly with the following fields:
- "ai_score" (float): The score you award to the student.
- "ai_feedback" (string): Your feedback for the student, including strengths and areas for improvement.
- "confidence" (float): Your confidence in this grading between 0.0 and 1.0.
- "rubric_scores" (dict mapping criteria name to float score): Optional detailed scores if rubrics were provided.
"""

        try:
            response_text = gemini_service.generate_text(
                prompt=prompt,
                user=current_user,
                is_complex=True, # Grading requires high reasoning
                temperature=0.2
            )

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}

            ai_score = float(data.get("ai_score", 0.0))
            confidence = float(data.get("confidence", 0.0))
            needs_manual_review = confidence < threshold

            rubric_scores_json = None
            if "rubric_scores" in data:
                rubric_scores_json = json.dumps(data["rubric_scores"])

            grading_result = AIGradingResult(
                student_answer_id=answer.id,
                ai_score=ai_score,
                ai_feedback=data.get("ai_feedback", "No feedback generated"),
                confidence=confidence,
                rubric_scores=rubric_scores_json,
                needs_manual_review=needs_manual_review,
                model_used=model_name or "gemini",
            )

            # Update the answer score if confidence is high enough
            if not needs_manual_review:
                answer.points_awarded = ai_score
                # For example, consider correct if score > 50% of max points
                if question.points and ai_score >= (question.points * 0.5):
                    answer.is_correct = True
                else:
                    answer.is_correct = False

            db.add(grading_result)
            db.commit()
            db.refresh(grading_result)
            return grading_result

        except Exception as e:
            logger.error(f"Grading failed for answer {answer_id}: {e}")
            return None

    @staticmethod
    def get_grading_result(db: Session, submission_id: int) -> Optional[Any]:
        """Mock method for getting legacy essay grading results from ai_tools.py if needed."""
        # For compatibility with ai_tools.py EssayGradeResponse schema
        return None

    @staticmethod
    async def grade_essay(
        db: Session,
        submission_id: int,
        essay_text: str,
        rubric: Dict,
        max_score: int = 100,
        current_user: Any = None,
    ) -> Any:
        """
        Legacy mock for ai_tools.py
        Note: The actual AIGradingResult schema doesn't match ai_tools EssayGradeResponse.
        """
        prompt = f"""Expert Essay Grader. Max Score: {max_score}. 
Rubric: {rubric}
Essay: {essay_text}

Return JSON with: score, feedback, strengths (list), improvements (list)."""

        try:
            response_text = gemini_service.generate_text(
                prompt=prompt,
                user=current_user,
                is_complex=True,
                temperature=0.3
            )

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}

            # Returning dict matching EssayGradeResponse
            return {
                "submission_id": submission_id,
                "score": float(data.get("score", 0)),
                "feedback": data.get("feedback", "No feedback"),
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", []),
                "grammar_score": data.get("grammar_score", 0),
                "originality_score": data.get("originality_score", 0)
            }
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            raise e
