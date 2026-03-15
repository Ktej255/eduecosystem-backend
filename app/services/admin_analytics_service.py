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
import re
from app.services.gemini_service import gemini_service
from app.models.drill import DrillSession, CurriculumInsight

logger = logging.getLogger(__name__)

class AdminAnalyticsService:
    """Service for admin analytics and AI-powered educational insights"""
    
    async def get_student_performance(
        self,
        db: Session,
        student_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get summarized performance for a single student."""
        query = db.query(
            func.count(DrillSession.id).label('total_drills'),
            func.avg(DrillSession.overall_score).label('avg_score'),
            func.avg(DrillSession.improvement).label('avg_improvement')
        ).filter(DrillSession.student_id == student_id)
        
        if start_date: query = query.filter(DrillSession.date >= start_date)
        if end_date: query = query.filter(DrillSession.date <= end_date)
        
        stats = query.first()
        return {
            "total_drills": int(stats.total_drills or 0),
            "average_score": round(float(stats.avg_score or 0), 1),
            "average_improvement": round(float(stats.avg_improvement or 0), 1)
        }

    async def get_aggregate_analytics(
        self,
        db: Session,
        gs_paper: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get aggregate metrics for all students."""
        query = db.query(
            func.count(func.distinct(DrillSession.student_id)).label('total_students'),
            func.count(DrillSession.id).label('total_drills'),
            func.avg(DrillSession.overall_score).label('avg_score'),
            func.avg(DrillSession.improvement).label('avg_improvement')
        )
        
        if gs_paper:
            query = query.filter(DrillSession.gs_paper == gs_paper)
        
        if start_date: query = query.filter(DrillSession.date >= start_date)
        if end_date: query = query.filter(DrillSession.date <= end_date)

        stats = query.first()
        return {
            "total_students": int(stats.total_students or 0),
            "total_drills": int(stats.total_drills or 0),
            "average_score": round(float(stats.avg_score or 0), 1),
            "average_improvement": round(float(stats.avg_improvement or 0), 1)
        }

    async def get_topic_performance(self, db: Session, gs_paper: Optional[str] = None) -> List[Dict]:
        """Break down performance by topic."""
        query = db.query(
            DrillSession.topic,
            func.count(DrillSession.id).label('total_attempts'),
            func.avg(DrillSession.overall_score).label('avg_score'),
            func.avg(DrillSession.improvement).label('avg_improvement')
        )
        
        if gs_paper:
            query = query.filter(DrillSession.gs_paper == gs_paper)
            
        topics = query.group_by(DrillSession.topic).all()
        
        return [
            {
                "topic": t.topic or "Miscellaneous",
                "total_attempts": int(t.total_attempts),
                "average_score": round(float(t.avg_score or 0), 1),
                "average_improvement": round(float(t.avg_improvement or 0), 1)
            }
            for t in topics
        ]

    async def get_daily_trends(self, db: Session, days: int = 30) -> Dict:
        """Get daily performance averages."""
        start_date = date.today() - timedelta(days=days)
        daily_stats = db.query(
            DrillSession.date,
            func.avg(DrillSession.overall_score).label('avg_score')
        ).filter(DrillSession.date >= start_date).group_by(DrillSession.date).all()
        
        return {
            "trends": [
                {
                    "date": str(s.date), 
                    "score": round(float(s.avg_score or 0), 1)
                } 
                for s in daily_stats
            ]
        }

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
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get data points for prompt
        topic_stats = await self.get_topic_performance(db, gs_paper)
        aggregate = await self.get_aggregate_analytics(db, gs_paper, start_date, end_date)
        
        topic_summary = "\n".join([f"- {t['topic']}: {t['average_score']}% over {t['total_attempts']} attempts" for t in topic_stats[:10]])

        prompt = f"""You are an expert UPSC Educational Analyst. 
Based on student performance data for {gs_paper} over the last {days} days:
- Overall Avg Score: {aggregate['average_score']}%
- Total Drills: {aggregate['total_drills']}
- Topic Breakdown:
{topic_summary}

Provide curriculum recommendations and identify performance gaps.
Return JSON ONLY:
{{
    "overall_assessment": "paragraph summary",
    "recommendations": [
        {{ "topic": "name", "suggested_action": "description", "priority": "high/medium/low" }}
    ],
    "content_gaps": ["list of concepts where students score < 50%"],
    "high_performing_topics": ["list of topics > 75%"]
}}"""

        try:
            response = gemini_service.generate_text(
                prompt=prompt,
                user=admin_user,
                is_complex=True,
                temperature=0.3
            )
            
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            return json.loads(json_match.group()) if json_match else {"error": "Failed to parse AI response"}
            
        except Exception as e:
            logger.error(f"Curriculum insights failed: {e}")
            return {"error": "AI analysis unavailable"}

# Global instance
admin_analytics_service = AdminAnalyticsService()
