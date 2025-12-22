"""
Quiz Generator Service

Automated quiz generation from course content using GPT-4.
"""

import openai
import os
import logging
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ai_features import AIGeneratedQuiz, AIUsageLog

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


class QuizGeneratorService:
    """
    Generate quizzes from course content using AI.
    """

    @staticmethod
    async def generate_quiz(
        db: Session,
        course_id: int,
        lesson_id: Optional[int],
        content: str,
        num_questions: int = 10,
        difficulty: str = "medium",
        question_types: List[str] = None,
        user_id: int = None,
    ) -> AIGeneratedQuiz:
        """
        Generate a quiz from course content.

        Args:
            db: Database session
            course_id: ID of the course
            lesson_id: Optional lesson ID
            content: Source content for quiz generation
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', or 'hard'
            question_types: List of question types to include
            user_id: ID of the user requesting generation

        Returns:
            AIGeneratedQuiz object with generated questions
        """
        if question_types is None:
            question_types = ["mcq", "true_false"]

        try:
            # Build prompt
            prompt = QuizGeneratorService._build_quiz_prompt(
                content, num_questions, difficulty, question_types
            )

            # Call GPT-4
            start_time = datetime.now()
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator creating high-quality quiz questions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Moderate creativity
                max_tokens=2000,
            )
            generation_time = (datetime.now() - start_time).total_seconds()

            # Parse response
            result_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = QuizGeneratorService._calculate_cost(tokens_used, "gpt-4")

            # Extract questions
            questions = QuizGeneratorService._parse_quiz_response(result_text)

            # Create AIGeneratedQuiz
            quiz = AIGeneratedQuiz(
                course_id=course_id,
                lesson_id=lesson_id,
                source_content=content[:1000],  # Store excerpt
                difficulty_level=difficulty,
                num_questions=num_questions,
                question_types=question_types,
                questions=questions,
                model_used="gpt-4",
                generation_cost=cost,
                generation_time=generation_time,
                created_by=user_id,
            )
            db.add(quiz)

            # Log usage
            if user_id:
                usage_log = AIUsageLog(
                    user_id=user_id,
                    feature="quiz_generation",
                    model_used="gpt-4",
                    tokens_used=tokens_used,
                    estimated_cost=cost,
                    success=True,
                )
                db.add(usage_log)

            db.commit()
            db.refresh(quiz)

            logger.info(
                f"Quiz generated successfully. {num_questions} questions created."
            )
            return quiz

        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            if user_id:
                usage_log = AIUsageLog(
                    user_id=user_id,
                    feature="quiz_generation",
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
    def _build_quiz_prompt(
        content: str, num_questions: int, difficulty: str, question_types: List[str]
    ) -> str:
        """
        Build the quiz generation prompt.
        """
        type_descriptions = {
            "mcq": "Multiple choice questions with 4 options",
            "true_false": "True/False questions",
            "short_answer": "Short answer questions",
        }

        types_text = ", ".join([type_descriptions.get(t, t) for t in question_types])

        prompt = f"""Generate {num_questions} quiz questions from the following content.

CONTENT:
{content}

REQUIREMENTS:
- Difficulty: {difficulty}
- Question types: {types_text}
- Include explanations for each answer
- Align with Bloom's Taxonomy (remember, understand, apply, analyze, evaluate, create)
- Ensure questions test understanding, not just memorization

Please provide your response in the following JSON format:
{{
    "questions": [
        {{
            "question": "<question text>",
            "type": "<mcq|true_false|short_answer>",
            "options": ["A", "B", "C", "D"],  // Only for MCQ
            "correct_answer": "<answer>",
            "explanation": "<why this is correct>",
            "difficulty": "<easy|medium|hard>",
            "bloom_level": "<remember|understand|apply|analyze|evaluate|create>",
            "points": <1-5>
        }}
    ]
}}

Generate exactly {num_questions} questions."""
        return prompt

    @staticmethod
    def _parse_quiz_response(response_text: str) -> List[Dict]:
        """
        Parse GPT-4 response into structured quiz questions.
        """
        try:
            # Extract JSON
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("questions", [])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse quiz JSON: {e}")

        # Fallback
        return []

    @staticmethod
    def _calculate_cost(tokens: int, model: str) -> float:
        """Calculate API cost."""
        pricing = {"gpt-4": 0.03 / 1000, "gpt-3.5-turbo": 0.002 / 1000}
        return tokens * pricing.get(model, 0.03 / 1000)

    @staticmethod
    def get_generated_quiz(db: Session, quiz_id: int) -> Optional[AIGeneratedQuiz]:
        """Retrieve a generated quiz."""
        return db.query(AIGeneratedQuiz).filter(AIGeneratedQuiz.id == quiz_id).first()

    @staticmethod
    def rate_quiz(db: Session, quiz_id: int, rating: int, notes: str = None):
        """
        Rate the quality of a generated quiz (instructor feedback).
        """
        quiz = db.query(AIGeneratedQuiz).filter(AIGeneratedQuiz.id == quiz_id).first()
        if quiz:
            quiz.instructor_rating = rating
            quiz.review_notes = notes
            # Calculate quality score based on rating
            quiz.quality_score = (rating / 5.0) * 100
            db.commit()
