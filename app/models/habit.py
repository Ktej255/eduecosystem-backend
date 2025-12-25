"""
Habit Tracking System
Track daily habits, build consistency, and earn coins for good habits.
Designed for building student discipline and routine.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List, Dict


class HabitTemplate(Base):
    """Predefined habits that students can adopt"""
    __tablename__ = "habit_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # mindfulness, study, health, productivity
    icon = Column(String(50), default="✨")  # Emoji icon
    
    # Recommended settings
    recommended_time = Column(String(20), nullable=True)  # "7:00 AM", "Before bed"
    duration_minutes = Column(Integer, default=10)
    
    # Rewards
    coins_per_completion = Column(Integer, default=5)
    streak_bonus_multiplier = Column(Float, default=1.5)
    
    # Difficulty/Level
    difficulty = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserHabit(Base):
    """User's active habits"""
    __tablename__ = "user_habits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("habit_templates.id"), nullable=True)
    
    # Custom habit details (if not from template)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="✨")
    category = Column(String(50), default="custom")
    
    # Schedule
    reminder_time = Column(String(20), nullable=True)  # "07:00"
    frequency = Column(String(20), default="daily")  # daily, weekdays, custom
    
    # Streak tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    
    # Coins
    coins_per_completion = Column(Integer, default=5)
    total_coins_earned = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_completed_date = Column(Date, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="habits")
    template = relationship("HabitTemplate", backref="user_habits")
    
    def complete_today(self) -> Dict:
        """Mark habit as completed for today"""
        today = date.today()
        result = {
            "already_completed": False,
            "streak_continued": False,
            "coins_earned": 0,
            "streak_bonus": False,
            "new_streak": self.current_streak
        }
        
        if self.last_completed_date == today:
            result["already_completed"] = True
            return result
        
        # Check streak
        if self.last_completed_date:
            days_since = (today - self.last_completed_date).days
            if days_since == 1:
                # Streak continues
                self.current_streak += 1
                result["streak_continued"] = True
            elif days_since > 1:
                # Streak broken, start fresh
                self.current_streak = 1
        else:
            # First completion
            self.current_streak = 1
            result["streak_continued"] = True
        
        self.last_completed_date = today
        self.total_completions += 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        # Calculate coins
        coins = self.coins_per_completion
        if self.current_streak >= 7:
            coins = int(coins * 1.5)  # 50% bonus for 7+ day streak
            result["streak_bonus"] = True
        elif self.current_streak >= 30:
            coins = coins * 2  # Double for 30+ day streak
            result["streak_bonus"] = True
        
        result["coins_earned"] = coins
        result["new_streak"] = self.current_streak
        self.total_coins_earned += coins
        
        return result


class HabitCompletion(Base):
    """Log of individual habit completions"""
    __tablename__ = "habit_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    habit_id = Column(Integer, ForeignKey("user_habits.id"), nullable=False, index=True)
    
    completed_date = Column(Date, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional notes/reflection
    notes = Column(Text, nullable=True)
    mood_before = Column(Integer, nullable=True)  # 1-5 scale
    mood_after = Column(Integer, nullable=True)
    
    coins_earned = Column(Integer, default=0)
    streak_at_completion = Column(Integer, default=1)


# Predefined habit templates
HABIT_TEMPLATES = [
    # Mindfulness
    {"name": "Morning Meditation", "category": "mindfulness", "icon": "🧘", "description": "Start your day with 10 minutes of mindful breathing", "recommended_time": "6:00 AM", "duration_minutes": 10, "coins_per_completion": 10},
    {"name": "Gratitude Journal", "category": "mindfulness", "icon": "📝", "description": "Write 3 things you're grateful for", "recommended_time": "Before bed", "duration_minutes": 5, "coins_per_completion": 5},
    {"name": "Mindful Walk", "category": "mindfulness", "icon": "🚶", "description": "Walk for 10 minutes without phone distractions", "recommended_time": "Evening", "duration_minutes": 10, "coins_per_completion": 8},
    
    # Study
    {"name": "Feynman Review", "category": "study", "icon": "📚", "description": "Explain one topic you learned today in simple words", "recommended_time": "After study", "duration_minutes": 10, "coins_per_completion": 15},
    {"name": "Spaced Recall", "category": "study", "icon": "🔄", "description": "Review your retention dashboard and complete due topics", "recommended_time": "Evening", "duration_minutes": 15, "coins_per_completion": 12},
    {"name": "Connect Concepts", "category": "study", "icon": "🔗", "description": "Link one new concept to something you already know", "recommended_time": "After learning", "duration_minutes": 5, "coins_per_completion": 8},
    
    # Health
    {"name": "Water Intake", "category": "health", "icon": "💧", "description": "Drink 8 glasses of water today", "recommended_time": "Throughout day", "duration_minutes": 1, "coins_per_completion": 5},
    {"name": "Sleep Before 11", "category": "health", "icon": "😴", "description": "Be in bed by 11 PM", "recommended_time": "10:30 PM", "duration_minutes": 0, "coins_per_completion": 10},
    {"name": "Morning Stretch", "category": "health", "icon": "🤸", "description": "5 minutes of stretching after waking", "recommended_time": "6:30 AM", "duration_minutes": 5, "coins_per_completion": 5},
    
    # Productivity
    {"name": "Plan Tomorrow", "category": "productivity", "icon": "📋", "description": "Write down 3 priorities for tomorrow", "recommended_time": "Before bed", "duration_minutes": 5, "coins_per_completion": 5},
    {"name": "No Phone Hour", "category": "productivity", "icon": "📵", "description": "1 hour of focused work without phone", "recommended_time": "Morning", "duration_minutes": 60, "coins_per_completion": 15},
    {"name": "Email Zero", "category": "productivity", "icon": "📧", "description": "Clear your inbox once today", "recommended_time": "Afternoon", "duration_minutes": 15, "coins_per_completion": 8},
]
