"""
AI Service Integration (Refactored 2025)
Now wraps GeminiService for unified tiered access and fallback.
"""

import os
from typing import Optional, List, Dict
from app.services.gemini_service import gemini_service

class AIService:
    """
    Unified AI service wrapper.
    Now redirects all requests to the tiered GeminiService.
    """

    def __init__(self):
        # We no longer need local keys here, gemini_service handles them
        pass

    async def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: Optional[str] = None, # Legacy parameter, now ignored
        user: Any = None,
    ) -> str:
        """
        Redirects to the tiered gemini_service with cascading fallback.
        """
        # Combine system message and prompt for simple text generation if needed,
        # but gemini_service.generate_text is the primary entry point.
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
        
        # Use sync call for now as gemini_service implementation is currently sync
        # In a real async-heavy app, we'd make gemini_service async.
        return gemini_service.generate_text(
            prompt=full_prompt,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def generate_quiz_questions(
        self, content: str, num_questions: int = 5, difficulty: str = "medium", user: Any = None
    ) -> List[Dict]:
        """Generate quiz questions using tiered AI"""
        import json
        
        system_message = f"Generate {num_questions} {difficulty} multiple choice questions. Return JSON array ONLY."
        prompt = f"Content: {content}"
        
        response = gemini_service.generate_text(
            prompt=f"{system_message}\n\n{prompt}",
            user=user,
            is_complex=True, # Quizzes are complex
            max_tokens=2000
        )
        
        try:
            return json.loads(self._extract_json(response))
        except:
            return []

    async def grade_essay(self, essay: str, rubric: str, max_score: int = 100, user: Any = None) -> Dict:
        """Grade essay using Premium Tier AI"""
        import json
        system_message = f"Expert Essay Grader. Max Score: {max_score}. Return JSON."
        prompt = f"Rubric: {rubric}\n\nEssay: {essay}"
        
        response = gemini_service.generate_text(
            prompt=f"{system_message}\n\n{prompt}",
            user=user,
            is_complex=True, # Grading is complex (uses Pro)
            max_tokens=2000
        )
        
        try:
            return json.loads(self._extract_json(response))
        except:
            return {"score": 0, "feedback": "Error in grading service"}

    def _extract_json(self, text: str) -> str:
        """Helper to extract JSON from markdown wraps"""
        import re
        json_match = re.search(r"\[.*\]|\{.*\}", text, re.DOTALL)
        return json_match.group() if json_match else text

    # Add other legacy methods as shells if needed, or refactor callers
    async def chat_with_tutor(self, message: str, history: List[Dict[str, str]], context: Optional[str] = None, user: Any = None) -> str:
        return gemini_service.chat(messages=history + [{"role": "user", "content": message}], user=user, system_prompt=context)

# Global AI service instance
ai_service = AIService()
