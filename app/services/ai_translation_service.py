"""
AI Translation Service (Fresh 2025)
Standardized on Tiered Gemini AI for high-quality language processing.
"""

from typing import Optional, Any
import logging
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

async def translate_text_ai(
    text: str, source_language: str, target_language: str, preserve_html: bool = False, user: Any = None
) -> str:
    """Translate using Tiered Gemini AI"""
    
    prompt = f"Translate from {source_language} to {target_language}. "
    if preserve_html:
        prompt += "PRESERVE HTML TAGS. "
    prompt += f"Text: {text}"

    try:
        # Use tiered service (Translation is standard task)
        return gemini_service.generate_text(
            prompt=prompt,
            user=user,
            is_complex=False,
            temperature=0.3
        )
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text # Fallback to original
