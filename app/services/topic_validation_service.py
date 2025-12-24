"""
Topic Validation Service (Fresh 2025)
Uses Tiered Gemini AI for content relevance.
"""

import json
import logging
from typing import Dict, Any, Optional
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class TopicValidationService:
    async def extract_topic(self, content: str, user: Any = None) -> Dict:
        """Extract topic using Tiered Gemini AI"""
        prompt = f"Identify the main topic of this text: {content[:2000]}. Return JSON ONLY."
        try:
            response = gemini_service.generate_text(prompt=prompt, user=user)
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            return json.loads(json_match.group()) if json_match else {}
        except: return {}

topic_validation_service = TopicValidationService()
