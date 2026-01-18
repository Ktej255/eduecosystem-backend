from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.gamification import Streak, ActivityType
from app.services.coin_service import trigger_coin_reward

class GamificationService:
    @staticmethod
    def record_activity(db: Session, user: User, activity_type: str) -> dict:
        """
        Record activity and update streaks for both User model and Streak model.
        """
        now = datetime.utcnow()
        today = now.date()
        
        # 1. Update the specific activity streak
        streak = db.query(Streak).filter(
            Streak.user_id == user.id,
            Streak.activity_type == activity_type
        ).first()
        
        if not streak:
            streak = Streak(
                user_id=user.id,
                activity_type=activity_type,
                current_streak=1,
                longest_streak=1,
                last_activity_date=now
            )
            db.add(streak)
        else:
            last_date = streak.last_activity_date.date()
            if last_date == today:
                # Already active today, just update time
                pass
            elif last_date == today - timedelta(days=1):
                # Next day, increment
                streak.current_streak += 1
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
            else:
                # Missed a day, reset
                streak.current_streak = 1
            
            streak.last_activity_date = now
            db.add(streak)
            
        # 2. Update global User streak if it's a primary activity (login/daily_checkin)
        if activity_type in ["login", "daily_checkin"]:
            last_login_date = user.last_login.date() if user.last_login else None
            
            if last_login_date == today:
                # Already logged in today
                pass
            elif last_login_date == today - timedelta(days=1):
                user.streak_days += 1
                # Award coins via coin_service logic if not already handled
                # (We'll let coin_service handle the rewards to avoid duplication)
                pass
            else:
                user.streak_days = 1
            
            user.last_login = now
            db.add(user)
            
        db.commit()
        db.refresh(user)
        if streak:
            db.refresh(streak)
            
        return {
            "current_streak": streak.current_streak if streak else user.streak_days,
            "global_streak": user.streak_days,
            "last_activity": now
        }

    @staticmethod
    def get_user_streaks(db: Session, user_id: int) -> dict:
        streaks = db.query(Streak).filter(Streak.user_id == user_id).all()
        user = db.query(User).filter(User.id == user_id).first()
        
        result = {}
        for s in streaks:
            result[s.activity_type] = {
                "current": s.current_streak,
                "longest": s.longest_streak,
                "last_active": s.last_activity_date
            }
            
        result["global"] = {
            "current": user.streak_days if user else 0,
            "longest": user.streak_days if user else 0# Simplified
        }
        return result

gamification_service = GamificationService()
