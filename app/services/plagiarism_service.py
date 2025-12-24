"""
Plagiarism Detection Service (Fresh 2025)
Uses Tiered Gemini AI for pattern recognition.
"""

from typing import Dict, List, Optional, Any
from app.services.gemini_service import gemini_service

class PlagiarismService:
    @staticmethod
    async def check_ai_generation(text: str, user: Any = None) -> float:
        """Detect AI generation patterns using Tiered Gemini AI"""
        prompt = f"Analyze this text for AI-generation patterns. Text: {text[:1000]}. Return only a score 0-1."
        try:
            response = gemini_service.generate_text(prompt=prompt, user=user)
            return float(response.strip())
        except: return 0.0

plagiarism_service = PlagiarismService()
