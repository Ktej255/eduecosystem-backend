"""
Final seeding script for achievements - using simple ORM without relationships
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 60)
print("SEEDING ACHIEVEMENTS")
print("=" * 60)

from app.db.session import SessionLocal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class AchievementSimple(Base):
    """Simplified Achievement model for seeding only"""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(20), nullable=False)
    rarity = Column(String(20))
    icon = Column(String(50))
    coin_reward = Column(Integer)
    unlock_condition = Column(JSON, nullable=False)
    is_hidden = Column(Boolean)
    is_active = Column(Boolean)
    display_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))


achievements_data = [
    {
        "name": "First Steps",
        "description": "Complete your first lesson",
        "category": "learning",
        "rarity": "common",
        "icon": "🎯",
        "coin_reward": 50,
        "unlock_condition": {"type": "lesson_complete_count", "count": 1},
        "is_hidden": False,
        "is_active": True,
        "display_order": 1,
    },
    {
        "name": "Quiz Taker",
        "description": "Complete your first quiz",
        "category": "learning",
        "rarity": "common",
        "icon": "📝",
        "coin_reward": 75,
        "unlock_condition": {"type": "quiz_complete_count", "count": 1},
        "is_hidden": False,
        "is_active": True,
        "display_order": 2,
    },
    {
        "name": "Course Completer",
        "description": "Finish your first course",
        "category": "learning",
        "rarity": "rare",
        "icon": "🎓",
        "coin_reward": 500,
        "unlock_condition": {"type": "course_complete_count", "count": 1},
        "is_hidden": False,
        "is_active": True,
        "display_order": 3,
    },
    {
        "name": "Perfect Score",
        "description": "Get 100% on a quiz",
        "category": "mastery",
        "rarity": "rare",
        "icon": "⭐",
        "coin_reward": 150,
        "unlock_condition": {"type": "perfect_quiz_count", "count": 1},
        "is_hidden": False,
        "is_active": True,
        "display_order": 5,
    },
    {
        "name": "Ace Student",
        "description": "Get 100% on 5 different quizzes",
        "category": "mastery",
        "rarity": "epic",
        "icon": "🌟",
        "coin_reward": 750,
        "unlock_condition": {"type": "perfect_quiz_count", "count": 5},
        "is_hidden": False,
        "is_active": True,
        "display_order": 6,
    },
    {
        "name": "Social Butterfly",
        "description": "Write 10 course reviews",
        "category": "social",
        "rarity": "rare",
        "icon": "🦋",
        "coin_reward": 200,
        "unlock_condition": {"type": "review_write_count", "count": 10},
        "is_hidden": False,
        "is_active": True,
        "display_order": 8,
    },
    {
        "name": "Discussion Starter",
        "description": "Create 5 discussion threads",
        "category": "social",
        "rarity": "common",
        "icon": "💬",
        "coin_reward": 150,
        "unlock_condition": {"type": "discussion_thread_count", "count": 5},
        "is_hidden": False,
        "is_active": True,
        "display_order": 9,
    },
    {
        "name": "Streak Starter",
        "description": "Maintain a 3-day learning streak",
        "category": "streak",
        "rarity": "common",
        "icon": "🔥",
        "coin_reward": 100,
        "unlock_condition": {"type": "streak_days", "days": 3},
        "is_hidden": False,
        "is_active": True,
        "display_order": 11,
    },
    {
        "name": "Streak Champion",
        "description": "Maintain a 7-day learning streak",
        "category": "streak",
        "rarity": "rare",
        "icon": "🔥🔥",
        "coin_reward": 200,
        "unlock_condition": {"type": "streak_days", "days": 7},
        "is_hidden": False,
        "is_active": True,
        "display_order": 12,
    },
    {
        "name": "Streak Legend",
        "description": "Maintain a 30-day learning streak",
        "category": "streak",
        "rarity": "legendary",
        "icon": "🔥🔥🔥",
        "coin_reward": 1000,
        "unlock_condition": {"type": "streak_days", "days": 30},
        "is_hidden": False,
        "is_active": True,
        "display_order": 13,
    },
]


def seed():
    db = SessionLocal()
    try:
        # Check existing
        count = db.query(AchievementSimple).count()
        if count > 0:
            print(f"⚠️  {count} achievements already exist. Clearing...")
            db.query(AchievementSimple).delete()
            db.commit()

        # Insert new
        for data in achievements_data:
            ach = AchievementSimple(**data)
            db.add(ach)
            print(f"  ✓ {data['name']}")

        db.commit()
        print(f"\n✅ Successfully seeded {len(achievements_data)} achievements!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("=" * 60)
