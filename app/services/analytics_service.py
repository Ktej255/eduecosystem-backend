from sqlalchemy.orm import Session
from app.models.user import User
from app.models.drill import DrillResult
from app.models.gamification import Streak
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AnalyticsService:
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
