"""
AI Task Router Service (Refactored 2025)
Provides task classification but uses GeminiService for actual execution.
"""

import logging
from typing import Optional, Dict, Any
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class AIRouter:
    """
    Simplified AI Router.
    Handles task categorization but delegates execution to the unified GeminiService.
    """
    
    async def route(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        user: Any = None,
        is_complex: bool = False
    ) -> Dict[str, Any]:
        """
        Routes the task to the tiered AI service.
        """
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
        
        # Delegate to the cascading service
        response = gemini_service.generate_text(
            prompt=full_prompt,
            user=user,
            is_complex=is_complex,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response,
            "status": "success"
        }

# Global router instance
ai_router = AIRouter()
