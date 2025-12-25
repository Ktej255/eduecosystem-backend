"""
Mastery Level System
Track student progress through skill levels with XP, badges, and unlocked content.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class MasteryLevel(Base):
    """User's mastery level and XP tracking"""
    __tablename__ = "mastery_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Current level
    level = Column(Integer, default=1)
    level_name = Column(String(50), default="Beginner")
    
    # XP tracking
    current_xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    xp_to_next_level = Column(Integer, default=100)
    
    # Badges earned
    badges = Column(String(500), default="[]")  # JSON list of badge IDs
    
    # Statistics
    topics_mastered = Column(Integer, default=0)
    habits_completed = Column(Integer, default=0)
    total_study_minutes = Column(Integer, default=0)
    
    # Timestamps
    level_up_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="mastery_level")
    
    def add_xp(self, amount: int, source: str = "unknown") -> dict:
        """Add XP and check for level up"""
        import json
        
        self.current_xp += amount
        self.total_xp += amount
        
        result = {
            "xp_gained": amount,
            "leveled_up": False,
            "new_level": self.level,
            "new_level_name": self.level_name,
            "new_badges": []
        }
        
        # Check for level up
        while self.current_xp >= self.xp_to_next_level:
            self.current_xp -= self.xp_to_next_level
            self.level += 1
            self.level_name = LEVEL_NAMES.get(self.level, f"Level {self.level}")
            self.xp_to_next_level = self._calculate_xp_required(self.level)
            self.level_up_at = func.now()
            result["leveled_up"] = True
            result["new_level"] = self.level
            result["new_level_name"] = self.level_name
            
            # Award level-up badges
            badge = LEVEL_BADGES.get(self.level)
            if badge:
                badges = json.loads(self.badges) if self.badges else []
                badges.append(badge)
                self.badges = json.dumps(badges)
                result["new_badges"].append(badge)
        
        return result
    
    def _calculate_xp_required(self, level: int) -> int:
        """XP required for next level (exponential growth)"""
        base_xp = 100
        return int(base_xp * (1.5 ** (level - 1)))


# Level progression
LEVEL_NAMES = {
    1: "Beginner",
    2: "Novice",
    3: "Apprentice",
    4: "Student",
    5: "Practitioner",
    6: "Scholar",
    7: "Adept",
    8: "Expert",
    9: "Master",
    10: "Grandmaster",
    11: "Sage",
    12: "Enlightened"
}

LEVEL_BADGES = {
    2: {"id": "first_steps", "name": "First Steps", "icon": "🌱", "description": "Reached Level 2"},
    5: {"id": "practitioner", "name": "Practitioner", "icon": "⭐", "description": "Reached Level 5"},
    7: {"id": "adept", "name": "Adept", "icon": "🔥", "description": "Reached Level 7"},
    10: {"id": "grandmaster", "name": "Grandmaster", "icon": "👑", "description": "Reached Level 10"},
    12: {"id": "enlightened", "name": "Enlightened", "icon": "🌟", "description": "Achieved Enlightenment"}
}

# XP sources
XP_REWARDS = {
    "meditation_complete": 10,
    "tutorial_finish": 15,
    "retention_review": 8,
    "midnight_test_pass": 20,
    "midnight_test_perfect": 35,
    "habit_complete": 5,
    "streak_7_day": 50,
    "streak_30_day": 150,
    "connect_dots": 10,
    "feynman_summary": 25,
    "course_complete": 100,
}
