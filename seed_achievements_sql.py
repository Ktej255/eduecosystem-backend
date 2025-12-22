"""
Direct SQL seeding for achievements to bypass ORM relationship issues
"""

import sqlite3
import json

# Achievement data
achievements = [
    (
        "First Steps",
        "Complete your first lesson",
        "learning",
        "common",
        "🎯",
        50,
        json.dumps({"type": "lesson_complete_count", "count": 1}),
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
        json.dumps({"type": "quiz_complete_count", "count": 1}),
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
        json.dumps({"type": "course_complete_count", "count": 1}),
        0,
        1,
        3,
    ),
    (
        "Curious Mind",
        "Enroll in 10 different courses",
        "explorer",
        "rare",
        "🧠",
        250,
        json.dumps({"type": "enrollment_count", "count": 10}),
        0,
        1,
        4,
    ),
    (
        "Perfect Score",
        "Get 100% on a quiz",
        "mastery",
        "rare",
        "⭐",
        150,
        json.dumps({"type": "perfect_quiz_count", "count": 1}),
        0,
        1,
        5,
    ),
    (
        "Ace Student",
        "Get 100% on 5 different quizzes",
        "mastery",
        "epic",
        "🌟",
        750,
        json.dumps({"type": "perfect_quiz_count", "count": 5}),
        0,
        1,
        6,
    ),
    (
        "Assignment Ace",
        "Get A grade on 5 assignments",
        "mastery",
        "epic",
        "📚",
        500,
        json.dumps({"type": "assignment_a_grade_count", "count": 5}),
        0,
        1,
        7,
    ),
    (
        "Social Butterfly",
        "Write 10 course reviews",
        "social",
        "rare",
        "🦋",
        200,
        json.dumps({"type": "review_write_count", "count": 10}),
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
        json.dumps({"type": "discussion_thread_count", "count": 5}),
        0,
        1,
        9,
    ),
    (
        "Helpful Hand",
        "Get 25 helpful votes on your posts",
        "social",
        "epic",
        "🤝",
        300,
        json.dumps({"type": "helpful_votes_count", "count": 25}),
        0,
        1,
        10,
    ),
    (
        "Streak Starter",
        "Maintain a 3-day learning streak",
        "streak",
        "common",
        "🔥",
        100,
        json.dumps({"type": "streak_days", "days": 3}),
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
        json.dumps({"type": "streak_days", "days": 7}),
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
        json.dumps({"type": "streak_days", "days": 30}),
        0,
        1,
        13,
    ),
    (
        "Certificate Collector",
        "Earn 3 course certificates",
        "dedicated",
        "epic",
        "🏆",
        750,
        json.dumps({"type": "certificate_count", "count": 3}),
        0,
        1,
        14,
    ),
    (
        "Live Learner",
        "Attend 5 live classes",
        "dedicated",
        "rare",
        "📹",
        300,
        json.dumps({"type": "live_class_attend_count", "count": 5}),
        0,
        1,
        15,
    ),
    (
        "Bookworm",
        "Create 50 course notes",
        "dedicated",
        "rare",
        "📖",
        200,
        json.dumps({"type": "notes_create_count", "count": 50}),
        0,
        1,
        16,
    ),
    (
        "Early Bird",
        "Complete a lesson before 8 AM",
        "special",
        "common",
        "🌅",
        50,
        json.dumps({"type": "lesson_before_hour", "hour": 8}),
        1,
        1,
        17,
    ),
    (
        "Night Owl",
        "Complete a lesson after 10 PM",
        "special",
        "common",
        "🦉",
        50,
        json.dumps({"type": "lesson_after_hour", "hour": 22}),
        1,
        1,
        18,
    ),
    (
        "Weekend Warrior",
        "Complete 3 lessons on a weekend",
        "special",
        "rare",
        "⚔️",
        150,
        json.dumps({"type": "weekend_lessons", "count": 3}),
        1,
        1,
        19,
    ),
    (
        "Platinum Learner",
        "Earn 10,000 total coins",
        "special",
        "legendary",
        "💎",
        2000,
        json.dumps({"type": "total_coins", "amount": 10000}),
        0,
        1,
        20,
    ),
]


def seed():
    print("=" * 60)
    print("SEEDING ACHIEVEMENTS (Direct SQL)")
    print("=" * 60)

    # Connect to correct database
    conn = sqlite3.connect(
        "d:/Graphology/Master Software/Eduecosystem/backend/eduecosystem.db"
    )
    cursor = conn.cursor()

    try:
        # Check existing
        cursor.execute("SELECT COUNT(*) FROM achievements")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"\n⚠️  {count} achievements exist. Clearing...")
            cursor.execute("DELETE FROM achievements")

        # Insert achievements
        for ach in achievements:
            cursor.execute(
                """
                INSERT INTO achievements 
                (name, description, category, rarity, icon, coin_reward, unlock_condition, is_hidden, is_active, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                ach,
            )
            print(f"  ✓ {ach[0]}")

        conn.commit()
        print(f"\n✅ Successfully seeded {len(achievements)} achievements!")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM achievements")
        final_count = cursor.fetchone()[0]
        print(f"   Total achievements in database: {final_count}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        import traceback

        traceback.print_exc()
    finally:
        conn.close()

    print("=" * 60)


if __name__ == "__main__":
    seed()
