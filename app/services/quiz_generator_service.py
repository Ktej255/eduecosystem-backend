"""
Quiz Generator Service (Fresh 2025)
Standardized on Tiered Gemini AI for question generation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class QuizGeneratorService:
    @staticmethod
    async def generate_quiz(
        db: Session,
        content: str,
        num_questions: int = 10,
        difficulty: str = "medium",
        user: Any = None
    ) -> List[Dict]:
        """Generate quiz using Tiered Gemini AI"""
        
        prompt = f"Generate {num_questions} quiz questions from this content: {content}. Difficulty: {difficulty}. Return JSON ONLY."
        
        try:
            # Complex task = Pro for Premium
            response = gemini_service.generate_text(
                prompt=prompt,
                user=user,
                is_complex=True
            )
            
            import re
            json_match = re.search(r"\[.*\]|\{.*\}", response, re.DOTALL)
            return json.loads(json_match.group()) if json_match else []
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []

quiz_generator_service = QuizGeneratorService()
