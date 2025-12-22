"""
AI Grading Service

Automated essay grading using GPT-4 with rubric-based evaluation.
"""

import openai
import os
import logging
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ai_features import AIUsageLog
from app.models.quiz import AIGradingResult
from app.models.assignment import Submission

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


class AIGradingService:
    """
    Automated essay grading using GPT-4.
    """

    @staticmethod
    async def grade_essay(
        db: Session,
        submission_id: int,
        essay_text: str,
        rubric: Dict,
        max_score: int = 100,
        user_id: int = None,
    ) -> AIGradingResult:
        """
        Grade an essay using GPT-4 based on a rubric.

        Args:
            db: Database session
            submission_id: ID of the submission
            essay_text: The essay content to grade
            rubric: Grading rubric with criteria
            max_score: Maximum possible score
            user_id: ID of the user requesting grading

        Returns:
            AIGradingResult with score, feedback, and analysis
        """
        try:
            # Build the prompt
            prompt = AIGradingService._build_grading_prompt(
                essay_text, rubric, max_score
            )

            # Call GPT-4
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert essay grader. Provide constructive, detailed feedback.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1500,
            )

            # Parse the response
            result_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = AIGradingService._calculate_cost(tokens_used, "gpt-4")

            # Extract structured data from response
            grading_data = AIGradingService._parse_grading_response(
                result_text, max_score
            )

            # Create AIGradingResult
            grading_result = AIGradingResult(
                submission_id=submission_id,
                essay_text=essay_text,
                score=Decimal(str(grading_data["score"])),
                max_score=Decimal(str(max_score)),
                feedback=grading_data["feedback"],
                strengths=grading_data["strengths"],
                improvements=grading_data["improvements"],
                grammar_score=grading_data.get("grammar_score", 80),
                originality_score=grading_data.get("originality_score", 90),
                model_used="gpt-4",
                tokens_used=tokens_used,
                graded_at=datetime.utcnow(),
            )
            db.add(grading_result)

            # Log usage
            if user_id:
                usage_log = AIUsageLog(
                    user_id=user_id,
                    feature="essay_grading",
                    model_used="gpt-4",
                    tokens_used=tokens_used,
                    estimated_cost=cost,
                    success=True,
                )
                db.add(usage_log)

            db.commit()
            db.refresh(grading_result)

            logger.info(
                f"Essay graded successfully. Submission {submission_id}, Score: {grading_data['score']}"
            )
            return grading_result

        except Exception as e:
            logger.error(f"Essay grading failed: {str(e)}")
            # Log failure
            if user_id:
                usage_log = AIUsageLog(
                    user_id=user_id,
                    feature="essay_grading",
                    model_used="gpt-4",
                    tokens_used=0,
                    estimated_cost=0,
                    success=False,
                    error_message=str(e),
                )
                db.add(usage_log)
                db.commit()
            raise

    @staticmethod
    def _build_grading_prompt(essay_text: str, rubric: Dict, max_score: int) -> str:
        """
        Build the grading prompt for GPT-4.
        """
        rubric_text = "\n".join(
            [
                f"- {criterion}: {description}"
                for criterion, description in rubric.items()
            ]
        )

        prompt = f"""Grade the following essay based on the rubric below. Provide a score out of {max_score}.

RUBRIC:
{rubric_text}

ESSAY:
{essay_text}

Please provide your response in the following JSON format:
{{
    "score": <number 0-{max_score}>,
    "feedback": "<overall feedback paragraph>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "improvements": ["<improvement 1>", "<improvement 2>", ...],
    "grammar_score": <number 0-100>,
    "originality_score": <number 0-100>,
    "rubric_scores": {{
        "<criterion 1>": <score>,
        "<criterion 2>": <score>
    }}
}}

Be constructive and specific in your feedback."""
        return prompt

    @staticmethod
    def _parse_grading_response(response_text: str, max_score: int) -> Dict:
        """
        Parse GPT-4 response into structured grading data.
        """
        import json
        import re

        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Ensure score is within bounds
                data["score"] = max(0, min(max_score, data.get("score", 0)))
                return data
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, using fallback parsing")

        # Fallback: simple parsing
        return {
            "score": max_score * 0.75,  # Default to 75%
            "feedback": response_text,
            "strengths": ["Well-structured"],
            "improvements": ["Continue developing ideas"],
            "grammar_score": 80,
            "originality_score": 90,
        }

    @staticmethod
    def _calculate_cost(tokens: int, model: str) -> float:
        """
        Calculate estimated API cost.
        """
        # GPT-4 pricing (as of 2024)
        pricing = {
            "gpt-4": 0.03 / 1000,  # per 1K tokens
            "gpt-3.5-turbo": 0.002 / 1000,
        }
        return tokens * pricing.get(model, 0.03 / 1000)

    @staticmethod
    def get_grading_result(
        db: Session, submission_id: int
    ) -> Optional[AIGradingResult]:
        """
        Retrieve grading result for a submission.
        """
        return (
            db.query(AIGradingResult)
            .filter(AIGradingResult.submission_id == submission_id)
            .first()
        )

    @staticmethod
    async def regrade_with_feedback(
        db: Session, submission_id: int, instructor_feedback: str, user_id: int = None
    ) -> AIGradingResult:
        """
        Re-grade an essay considering instructor feedback.
        """
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError("Submission not found")

        # Build enhanced rubric with instructor feedback
        rubric = {
            "Content": "Accuracy and depth of content",
            "Organization": "Structure and flow",
            "Language": "Grammar and vocabulary",
            "Instructor Notes": instructor_feedback,
        }

        return await AIGradingService.grade_essay(
            db, submission_id, submission.content, rubric, 100, user_id
        )
