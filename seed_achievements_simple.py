"""
Simplified achievement seeding - direct insert approach
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from sqlalchemy import text

# Achievement data as raw SQL-friendly dicts
achievements = [
    (
        "First Steps",
        "Complete your first lesson",
        "learning",
        "common",
        "🎯",
        50,
        '{"type": "lesson_complete_count", "count": 1}',
        0,
        1,
        1,
    ),
    (
        "Quiz Taker",
        "Complete your first quiz",
        "learning",
        "common",
        "📝",
        75,
        '{"type": "quiz_complete_count", "count": 1}',
        0,
        1,
        2,
    ),
    (
        "Course Completer",
        "Finish your first course",
        "learning",
        "rare",
        "🎓",
        500,
        '{"type": "course_complete_count", "count": 1}',
        0,
        1,
        3,
    ),
    (
        "Perfect Score",
        "Get 100% on a quiz",
        "mastery",
        "rare",
        "⭐",
        150,
        '{"type": "perfect_quiz_count", "count": 1}',
        0,
        1,
        5,
    ),
    (
        "Social Butterfly",
        "Write 10 course reviews",
        "social",
        "rare",
        "🦋",
        200,
        '{"type": "review_write_count", "count": 10}',
        0,
        1,
        8,
    ),
    (
        "Discussion Starter",
        "Create 5 discussion threads",
        "social",
        "common",
        "💬",
        150,
        '{"type": "discussion_thread_count", "count": 5}',
        0,
        1,
        9,
    ),
    (
        "Streak Starter",
        "Maintain a 3-day learning streak",
        "streak",
        "common",
        "🔥",
        100,
        '{"type": "streak_days", "days": 3}',
        0,
        1,
        11,
    ),
    (
        "Streak Champion",
        "Maintain a 7-day learning streak",
        "streak",
        "rare",
        "🔥🔥",
        200,
        '{"type": "streak_days", "days": 7}',
        0,
        1,
        12,
    ),
    (
        "Streak Legend",
        "Maintain a 30-day learning streak",
        "streak",
        "legendary",
        "🔥🔥🔥",
        1000,
        '{"type": "streak_days", "days": 30}',
        0,
        1,
        13,
    ),
    (
        "Early Bird",
        "Complete a lesson before 8 AM",
        "special",
        "common",
        "🌅",
        50,
        '{"type": "lesson_before_hour", "hour": 8}',
        1,
        1,
        17,
    ),
]


def seed():
    db = SessionLocal()
    try:
        print("🌱 Seeding achievements directly...")

        # Check if achievements already exist
        result = db.execute(text("SELECT COUNT(*) FROM achievements"))
        count = result.scalar()

        if count > 0:
            print(f"  ⚠️  {count} achievements already exist. Skipping...")
            return

        # Insert achievements
        for ach in achievements:
            db.execute(
                text("""
                INSERT INTO achievements 
                (name, description, category, rarity, icon, coin_reward, unlock_condition, is_hidden, is_active, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """),
                ach,
            )

        db.commit()
        print(f"✅ Successfully seeded {len(achievements)} achievements!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
