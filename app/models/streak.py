"""
Streak & Engagement System
Tracks daily engagement, rewards consistency, and provides streak freeze tokens.
Integrates with coin system for rewards.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any


class UserStreak(Base):
    """Track user's daily engagement streak"""
    __tablename__ = "user_streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Current streak
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    
    # Streak freeze (protection tokens)
    freeze_tokens = Column(Integer, default=0)  # Free tokens to skip a day
    freeze_used_dates = Column(String(500), default="")  # JSON list of dates freeze was used
    
    # Last activity
    last_activity_date = Column(Date, nullable=True)
    last_activity_type = Column(String(50), nullable=True)  # meditation, retention, graphotherapy
    
    # Milestones
    total_active_days = Column(Integer, default=0)
    milestone_7_reached = Column(Boolean, default=False)
    milestone_30_reached = Column(Boolean, default=False)
    milestone_100_reached = Column(Boolean, default=False)
    
    # Coins earned from streaks
    total_streak_coins = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="streak_data")
    
    def check_and_update_streak(self, activity_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check activity and update streak.
        Returns dict with streak status and any rewards earned.
        """
        import json
        from datetime import date
        
        today = activity_date.date() if activity_date else date.today()
        result = {
            "streak_continued": False,
            "streak_broken": False,
            "freeze_used": False,
            "new_streak": self.current_streak,
            "coins_earned": 0,
            "milestone_reached": None,
            "message": ""
        }
        
        if self.last_activity_date is None:
            # First ever activity
            self.current_streak = 1
            self.last_activity_date = today
            self.total_active_days = 1
            result["streak_continued"] = True
            result["new_streak"] = 1
            result["message"] = "🔥 You started your streak! Day 1!"
            return result
        
        days_since_last = (today - self.last_activity_date).days
        
        if days_since_last == 0:
            # Already counted today
            result["message"] = "Already active today!"
            return result
            
        elif days_since_last == 1:
            # Perfect! Streak continues
            self.current_streak += 1
            self.total_active_days += 1
            self.last_activity_date = today
            
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            
            result["streak_continued"] = True
            result["new_streak"] = self.current_streak
            result["coins_earned"] = self._calculate_streak_reward()
            result["milestone_reached"] = self._check_milestones()
            result["message"] = f"🔥 Day {self.current_streak}! Keep going!"
            
        elif days_since_last == 2 and self.freeze_tokens > 0:
            # Missed one day but can use freeze
            self.freeze_tokens -= 1
            freeze_dates = json.loads(self.freeze_used_dates) if self.freeze_used_dates else []
            freeze_dates.append(str(today - timedelta(days=1)))
            self.freeze_used_dates = json.dumps(freeze_dates)
            
            self.current_streak += 1
            self.total_active_days += 1
            self.last_activity_date = today
            
            result["streak_continued"] = True
            result["freeze_used"] = True
            result["new_streak"] = self.current_streak
            result["message"] = f"❄️ Freeze used! Streak saved at Day {self.current_streak}!"
            
        else:
            # Streak broken
            old_streak = self.current_streak
            self.current_streak = 1
            self.last_activity_date = today
            self.total_active_days += 1
            
            result["streak_broken"] = True
            result["new_streak"] = 1
            result["message"] = f"💔 Streak broken (was {old_streak} days). Starting fresh!"
        
        return result
    
    def _calculate_streak_reward(self) -> int:
        """Calculate coin reward based on streak length"""
        streak = self.current_streak
        
        # Base rewards
        if streak <= 3:
            coins = 5
        elif streak <= 7:
            coins = 10
        elif streak <= 14:
            coins = 15
        elif streak <= 30:
            coins = 20
        else:
            coins = 25
        
        # Milestone bonuses
        if streak == 7:
            coins += 50  # Week bonus
        elif streak == 30:
            coins += 200  # Month bonus
        elif streak == 100:
            coins += 500  # Century bonus
        elif streak % 10 == 0:
            coins += 25  # Every 10 days
        
        self.total_streak_coins += coins
        return coins
    
    def _check_milestones(self) -> Optional[str]:
        """Check if a milestone was reached"""
        if self.current_streak >= 7 and not self.milestone_7_reached:
            self.milestone_7_reached = True
            self.freeze_tokens += 1  # Award a freeze token
            return "7_day"
        elif self.current_streak >= 30 and not self.milestone_30_reached:
            self.milestone_30_reached = True
            self.freeze_tokens += 2  # Award 2 freeze tokens
            return "30_day"
        elif self.current_streak >= 100 and not self.milestone_100_reached:
            self.milestone_100_reached = True
            self.freeze_tokens += 5  # Award 5 freeze tokens
            return "100_day"
        return None


class DailyActivity(Base):
    """Log of daily activities for streak tracking"""
    __tablename__ = "daily_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_date = Column(Date, nullable=False, index=True)
    
    # Activity types completed
    meditation_completed = Column(Boolean, default=False)
    retention_completed = Column(Boolean, default=False)
    graphotherapy_completed = Column(Boolean, default=False)
    
    # Points earned today
    coins_earned = Column(Integer, default=0)
    
    # Time spent
    total_minutes = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
