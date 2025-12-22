"""
Admin Analytics Service
Provides insights and analytics for admin portal using Grok AI
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from uuid import UUID

from app.models.drill import DrillSession, DrillDailySummary, DrillQuestion, CurriculumInsight
from app.models.user import User
from app.services.ai_service import ai_service
import json


class AdminAnalyticsService:
    """Service for admin analytics and insights"""
    
    async def get_student_performance(
        self,
        db: Session,
        student_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get individual student performance metrics"""
        
        query = db.query(DrillSession).filter(
            DrillSession.student_id == student_id,
            DrillSession.completed_at.isnot(None)
        )
        
        if start_date:
            query = query.filter(DrillSession.date >= start_date)
        if end_date:
            query = query.filter(DrillSession.date <= end_date)
        
        sessions = query.all()
        
        if not sessions:
            return {
                "student_id": str(student_id),
                "total_drills": 0,
                "average_score": 0,
                "average_improvement": 0
            }
        
        total_drills = len(sessions)
        avg_score = sum(s.overall_score or 0 for s in sessions) / total_drills
        avg_improvement = sum(s.improvement or 0 for s in sessions) / total_drills
        
        return {
            "student_id": str(student_id),
            "total_drills": total_drills,
            "average_score": round(avg_score, 2),
            "average_improvement": round(avg_improvement, 2),
            "sessions": [
                {
                    "date": s.date,
                    "question_number": s.question_number,
                    "before_score": s.before_score,
                    "after_score": s.after_score,
                    "improvement": s.improvement
                }
                for s in sessions
            ]
        }
    
    async def get_aggregate_analytics(
        self,
        db: Session,
        gs_paper: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Get aggregate analytics for all students"""
        
        query = db.query(DrillSession).filter(
            DrillSession.completed_at.isnot(None)
        )
        
        if gs_paper:
            query = query.join(DrillQuestion).filter(DrillQuestion.gs_paper == gs_paper)
        if start_date:
            query = query.filter(DrillSession.date >= start_date)
        if end_date:
            query = query.filter(DrillSession.date <= end_date)
        
        sessions = query.all()
        
        if not sessions:
            return {
                "total_students": 0,
                "total_drills": 0,
                "average_score": 0,
                "average_improvement": 0
            }
        
        # Unique students
        unique_students = len(set(s.student_id for s in sessions))
        
        # Aggregate metrics
        total_drills = len(sessions)
        avg_score = sum(s.overall_score or 0 for s in sessions) / total_drills
        avg_improvement = sum(s.improvement or 0 for s in sessions) / total_drills
        
        # Top performers
        student_scores = {}
        for s in sessions:
            if s.student_id not in student_scores:
                student_scores[s.student_id] = []
            student_scores[s.student_id].append(s.overall_score or 0)
        
        student_averages = {
            sid: sum(scores) / len(scores)
            for sid, scores in student_scores.items()
        }
        
        top_performers = sorted(
            student_averages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_students": unique_students,
            "total_drills": total_drills,
            "average_score": round(avg_score, 2),
            "average_improvement": round(avg_improvement, 2),
            "top_performers": [
                {"student_id": str(sid), "average_score": round(score, 2)}
                for sid, score in top_performers
            ]
        }
    
    async def get_topic_performance(
        self,
        db: Session,
        gs_paper: Optional[str] = None
    ) -> List[Dict]:
        """Get performance by topic"""
        
        query = db.query(
            DrillQuestion.topic,
            func.count(DrillSession.id).label('total_attempts'),
            func.avg(DrillSession.overall_score).label('avg_score'),
            func.avg(DrillSession.improvement).label('avg_improvement')
        ).join(
            DrillSession, DrillQuestion.id == DrillSession.question_id
        ).filter(
            DrillSession.completed_at.isnot(None)
        )
        
        if gs_paper:
            query = query.filter(DrillQuestion.gs_paper == gs_paper)
        
        results = query.group_by(DrillQuestion.topic).all()
        
        return [
            {
                "topic": r.topic,
                "total_attempts": r.total_attempts,
                "average_score": round(r.avg_score or 0, 2),
                "average_improvement": round(r.avg_improvement or 0, 2)
            }
            for r in results
        ]
    
    async def get_daily_trends(
        self,
        db: Session,
        days: int = 30
    ) -> List[Dict]:
        """Get daily performance trends"""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(
            DrillSession.date,
            func.count(func.distinct(DrillSession.student_id)).label('total_students'),
            func.avg(DrillSession.overall_score).label('avg_score'),
            func.avg(DrillSession.improvement).label('avg_improvement')
        ).filter(
            and_(
                DrillSession.date >= start_date,
                DrillSession.date <= end_date,
                DrillSession.completed_at.isnot(None)
            )
        ).group_by(DrillSession.date).order_by(DrillSession.date)
        
        results = query.all()
        
        return [
            {
                "date": str(r.date),
                "total_students": r.total_students,
                "average_score": round(r.avg_score or 0, 2),
                "average_improvement": round(r.avg_improvement or 0, 2)
            }
            for r in results
        ]
    
    async def generate_curriculum_insights(
        self,
        db: Session,
        gs_paper: str,
        days: int = 30
    ) -> Dict:
        """Generate AI-powered curriculum insights using Grok"""
        
        # Get aggregate data
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        aggregate = await self.get_aggregate_analytics(db, gs_paper, start_date, end_date)
        topic_performance = await self.get_topic_performance(db, gs_paper)
        
        # Identify low-performing topics
        low_performing = [
            t for t in topic_performance
            if t['average_score'] < 60
        ]
        
        # Identify high-performing topics
        high_performing = [
            t for t in topic_performance
            if t['average_score'] >= 80
        ]
        
        # Common challenges from recent sessions
        recent_sessions = db.query(DrillSession).join(DrillQuestion).filter(
            and_(
                DrillQuestion.gs_paper == gs_paper,
                DrillSession.date >= start_date,
                DrillSession.completed_at.isnot(None)
            )
        ).all()
        
        # Extract challenges from report data
        all_challenges = []
        for session in recent_sessions:
            if session.report_data and 'areas_for_improvement' in session.report_data:
                all_challenges.extend(session.report_data['areas_for_improvement'])
        
        # Count frequency of challenges
        from collections import Counter
        challenge_counts = Counter(all_challenges)
        common_challenges = [c for c, count in challenge_counts.most_common(5)]
        
        # Use Grok to generate insights
        system_message = """You are an expert educational analyst for UPSC preparation.
Analyze student performance data and provide actionable curriculum improvement recommendations.
Return your analysis as valid JSON only."""
        
        prompt = f"""Analyze the following student performance data for {gs_paper}:

**Overall Metrics (Last {days} days):**
- Total Students: {aggregate['total_students']}
- Total Drills Completed: {aggregate['total_drills']}
- Average Score: {aggregate['average_score']}%
- Average Improvement: {aggregate['average_improvement']}%

**Low-Performing Topics:**
{json.dumps(low_performing, indent=2)}

**High-Performing Topics:**
{json.dumps(high_performing, indent=2)}

**Common Student Challenges:**
{json.dumps(common_challenges, indent=2)}

Provide curriculum improvement recommendations in the following JSON format:
{{
    "overall_assessment": "Brief assessment of current curriculum effectiveness",
    "recommendations": [
        {{
            "category": "content_gap|difficulty_adjustment|new_topic|teaching_method",
            "priority": "high|medium|low",
            "topic": "Topic name if applicable",
            "description": "Detailed description of the issue",
            "suggested_action": "Specific action to take",
            "expected_impact": "Expected improvement"
        }}
    ],
    "content_gaps": ["List of topics that need more content or examples"],
    "difficulty_adjustments": ["Questions that are too easy or too hard"],
    "new_topics_suggested": ["New topics to add to curriculum"],
    "teaching_method_improvements": ["Suggested improvements to teaching approach"]
}}"""
        
        try:
            response = await ai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=2500,
                temperature=0.3,
                provider="grok"
            )
            
            insights = json.loads(response)
            
            # Store in database
            db_insight = CurriculumInsight(
                date=date.today(),
                gs_paper=gs_paper,
                total_students=aggregate['total_students'],
                average_score=aggregate['average_score'],
                common_challenges=common_challenges,
                high_performing_topics=[t['topic'] for t in high_performing],
                low_performing_topics=[t['topic'] for t in low_performing],
                ai_recommendations=insights
            )
            db.add(db_insight)
            db.commit()
            
            return insights
            
        except Exception as e:
            # Fallback insights
            return {
                "overall_assessment": f"Analysis for {gs_paper} based on {aggregate['total_students']} students",
                "recommendations": [
                    {
                        "category": "content_gap",
                        "priority": "high",
                        "topic": low_performing[0]['topic'] if low_performing else "General",
                        "description": "Low performance detected in this topic",
                        "suggested_action": "Add more examples and practice questions",
                        "expected_impact": "10-15% improvement in scores"
                    }
                ],
                "error": str(e)
            }


# Global instance
admin_analytics_service = AdminAnalyticsService()
