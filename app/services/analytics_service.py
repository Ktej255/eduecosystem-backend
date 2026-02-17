from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.drill import DrillResult
from app.models.gamification import Streak
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.shadow_mode import ShadowModeSession
from app.models.activity_log import ActivityLog
from app.models.submission import HandwritingSubmission
from app.models.meditation import MeditationExperience
from app.models.lesson_progress import LessonProgress
from sqlalchemy import func

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

    def get_focus_correlation(self, db: Session, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Correlates Meditation Focus Scores with Academic Lesson Completions.
        Returns a time-series dataset.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 1. Get daily average meditation focus scores
        meditation_data = db.query(
            func.date(MeditationExperience.post_recorded_at).label('date'),
            func.avg(MeditationExperience.post_focus_level).label('avg_focus')
        ).filter(
            MeditationExperience.user_id == user_id,
            MeditationExperience.post_recorded_at >= start_date,
            MeditationExperience.post_recorded_at.isnot(None)
        ).group_by(func.date(MeditationExperience.post_recorded_at)).all()
        
        # 2. Get daily lesson completions
        lesson_data = db.query(
            func.date(LessonProgress.completed_at).label('date'),
            func.count(LessonProgress.id).label('completions')
        ).filter(
            LessonProgress.user_id == user_id,
            LessonProgress.completed_at >= start_date
        ).group_by(func.date(LessonProgress.completed_at)).all()
        
        # 3. Merge data
        dataset = {}
        for d in meditation_data:
            dataset[str(d.date)] = {"date": str(d.date), "focus_score": float(d.avg_focus), "chapters_completed": 0}
            
        for d in lesson_data:
            date_str = str(d.date)
            if date_str in dataset:
                dataset[date_str]["chapters_completed"] = int(d.completions)
            else:
                dataset[date_str] = {"date": date_str, "focus_score": 0, "chapters_completed": int(d.completions)}
                
        # Sort by date
        sorted_data = sorted(dataset.values(), key=lambda x: x["date"])
        return sorted_data

    def create_event(self, db: Session, event_in: Any, user_id: Optional[int] = None) -> Any:
        """
        Create a new analytics event.
        """
        from app.models.analytics import AnalyticsEvent
        import json

        db_event = AnalyticsEvent(
            event_type=event_in.event_type,
            user_id=user_id or event_in.user_id,
            course_id=event_in.course_id,
            event_data=json.dumps(event_in.event_data) if event_in.event_data else None,
            session_id=event_in.session_id
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    def get_admin_overview(self, db: Session) -> Dict[str, Any]:
        """
        Aggregated stats for teacher/admin analytics dashboard.
        Returns real user counts, active user counts, and behavioral signal totals.
        """
        from app.models.analytics import AnalyticsEvent

        total_users = db.query(func.count(User.id)).scalar() or 0
        
        day_ago = datetime.utcnow() - timedelta(hours=24)
        active_24h = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
            ActivityLog.timestamp >= day_ago
        ).scalar() or 0

        # Behavioral signals in last 24h
        struggle_signals = db.query(func.count(AnalyticsEvent.id)).filter(
            AnalyticsEvent.event_type == 'struggle_signal',
            AnalyticsEvent.timestamp >= day_ago
        ).scalar() or 0

        # Total completions tracked via activity log
        total_completions = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.action.in_(['chapter_complete', 'topic_complete', 'lesson_complete'])
        ).scalar() or 0

        # Watch time approximation (study sessions * avg 25 min pomodoro)
        from app.models.study_session import StudySession
        total_sessions = db.query(func.count(StudySession.id)).scalar() or 0
        est_watch_hours = round(total_sessions * 25 / 60)

        return {
            "total_users": total_users,
            "active_students_24h": active_24h,
            "struggle_signals_24h": struggle_signals,
            "total_completions": total_completions,
            "est_watch_hours": est_watch_hours,
            "timestamp": datetime.utcnow().isoformat()
        }

analytics_service = AnalyticsService()
