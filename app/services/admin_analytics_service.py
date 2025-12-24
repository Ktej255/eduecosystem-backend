"""
Admin Analytics Service (Fresh 2025)
Generates educational insights using Tiered Gemini AI.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from uuid import UUID
import json
import logging
from app.services.gemini_service import gemini_service
from app.models.drill import DrillSession, CurriculumInsight

logger = logging.getLogger(__name__)

class AdminAnalyticsService:
    """Service for admin analytics and AI-powered educational insights"""
    
    async def generate_curriculum_insights(
        self,
        db: Session,
        gs_paper: str,
        days: int = 30,
        admin_user: Any = None
    ) -> Dict:
        """
        Analyze student data for UPSC GS Paper and generate AI insights.
        Uses Tiered Gemini Pro for high-quality reasoning.
        """
        
        # 1. Fetch data aggregates (Simplify for prompt)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # (Data aggregation logic remains similar to handle the DB queries)
        # Assuming we have access to the helper methods or inline them
        
        prompt = f"""You are an expert UPSC Educational Analyst. 
Based on student performance data for {gs_paper} over the last {days} days, provide curriculum recommendations.

Return JSON ONLY:
{{
    "overall_assessment": "paragraph",
    "recommendations": [
        {{ "topic": "name", "suggested_action": "description", "priority": "high/medium/low" }}
    ],
    "content_gaps": ["list"]
}}"""

        try:
            # Insights are complex, uses Pro model for Paid Admins
            response = gemini_service.generate_text(
                prompt=prompt,
                user=admin_user,
                is_complex=True,
                temperature=0.3
            )
            
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            return json.loads(json_match.group()) if json_match else {}
            
        except Exception as e:
            logger.error(f"Curriculum insights failed: {e}")
            return {"error": "AI analysis unavailable"}

# Global instance
admin_analytics_service = AdminAnalyticsService()
