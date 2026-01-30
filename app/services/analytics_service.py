from sqlalchemy.orm import Session
from app.models.user import User
from app.models.drill import DrillResult
from app.models.gamification import Streak
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.models.shadow_mode import ShadowModeSession
from app.models.activity_log import ActivityLog
from app.models.submission import HandwritingSubmission

class AnalyticsService:
    def get_dashboard_analytics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive analytics for user dashboard.
        """
        user = db.query(User).get(user_id)
        if not user:
            return {}

        # 1. Shadow Mode Stats
        shadow_sessions = db.query(ShadowModeSession).filter(
            ShadowModeSession.user_id == user_id,
            ShadowModeSession.is_active == False
        ).all()
        
        formatted_shadow = {
            "completed_days": len(shadow_sessions),
            "total_days": 7,
            "total_minutes": sum(s.duration_minutes or 0 for s in shadow_sessions),
            "avg_focus_score": sum(s.focus_score or 0 for s in shadow_sessions) / len(shadow_sessions) if shadow_sessions else 0
        }

        # 2. Attention Stats
        attention_logs = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id,
            ActivityLog.action == "attention_check"
        ).order_by(ActivityLog.timestamp.desc()).limit(10).all()
        
        recent_scores = []
        for log in attention_logs:
            try:
                recent_scores.append(float(log.details))
            except (ValueError, TypeError):
                pass
                
        formatted_attention = {
            "total_checks": db.query(ActivityLog).filter(
                ActivityLog.user_id == user_id,
                ActivityLog.action == "attention_check"
            ).count(),
            "average_focus": sum(recent_scores) / len(recent_scores) if recent_scores else 0,
            "recent_scores": recent_scores
        }

        # 3. Handwriting Stats
        formatted_handwriting = {
            "total_submissions": db.query(HandwritingSubmission).filter(
                HandwritingSubmission.user_id == user_id
            ).count()
        }

        # 5. Insights
        insights = []
        if user.streak_days >= 3:
            insights.append({
                "title": "On Fire!",
                "description": f"You're on a {user.streak_days} day streak. Keep it up!",
                "type": "success"
            })
        else:
             insights.append({
                "title": "Get Started",
                "description": "Start your streak today!",
                "type": "info"
            })


        return {
            "user": {
                "coins": user.coins,
                "streak_days": user.streak_days,
                "full_name": user.full_name
            },
            "shadow_mode": formatted_shadow,
            "attention": formatted_attention,
            "handwriting": formatted_handwriting,
            "weekly_activity": [],
            "insights": insights
        }

    def assess_student_risk(self, db: Session, student_id: int) -> Dict[str, Any]:
        """
        Calculates a risk score (0-100) for a student.
        Higher score = Higher risk of drop-out or failure.
        """
        risk_score = 0
        reasons = []

        # 1. Check Drill Performance (Last 5 drills)
        # If avg score < 50%, high risk.
        recent_results = db.query(DrillResult).filter(
            DrillResult.user_id == student_id
        ).order_by(DrillResult.completed_at.desc()).limit(5).all()

        if recent_results:
            avg_score = sum([r.score for r in recent_results]) / len(recent_results)
            if avg_score < 50:
                risk_score += 40
                reasons.append("Low Drill Scores (<50%)")
            elif avg_score < 70:
                risk_score += 15
                reasons.append("Mediocre Performance")
        else:
             # No drills taken might be a risk in itself if account is old
             pass

        # 2. Check Attendance / Activity (Streaks)
        # If no activity in last 7 days, high risk.
        streak = db.query(Streak).filter(
            Streak.user_id == student_id,
            Streak.activity_type == 'login' # or 'daily_checkin'
        ).first()

        if streak:
            days_since_active = (datetime.utcnow() - streak.last_activity_date).days
            if days_since_active > 7:
                risk_score += 30
                reasons.append(f"Inactive for {days_since_active} days")
            elif days_since_active > 3:
                risk_score += 10
        else:
            # Check user creation date
            user = db.query(User).get(student_id)
            if user and (datetime.utcnow() - user.created_at).days > 7:
                 risk_score += 30
                 reasons.append("No recorded activity")

        # 3. Cap Score
        risk_score = min(risk_score, 100)
        
        return {
            "risk_score": risk_score,
            "reasons": reasons,
            "status": "High" if risk_score >= 70 else "Medium" if risk_score >= 40 else "Low"
        }

    def get_at_risk_students(self, db: Session, threshold: int = 50) -> List[Dict[str, Any]]:
        """
        Get all students with risk score above threshold.
        """
        # In a real app, this would be optimized (batch processing or material view)
        # For now, we iterate recent active students or all students
        students = db.query(User).filter(User.role == "student").limit(50).all() 
        
        at_risk_list = []
        for student in students:
            assessment = self.assess_student_risk(db, student.id)
            if assessment["risk_score"] >= threshold:
                at_risk_list.append({
                    "id": student.id,
                    "name": student.full_name,
                    "email": student.email,
                    "risk_score": assessment["risk_score"],
                    "reasons": assessment["reasons"],
                    "status": assessment["status"]
                })
        
        # Sort by risk score desc
        at_risk_list.sort(key=lambda x: x["risk_score"], reverse=True)
        return at_risk_list

analytics_service = AnalyticsService()
