"""
Achievement Service

Handles achievement unlocking logic and predefined achievements.
Automatically checks and unlocks achievements based on user actions.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User
from app.models.achievement import (
    Achievement,
    UserAchievement,
    AchievementCategory,
    AchievementRarity,
)
from app.services.coin_service import award_coins
from datetime import datetime


def get_predefined_achievements() -> List[dict]:
    """
    Return list of all predefined achievements.
    These will be seeded into the database.
    """
    return [
        # Learning Category
        {
            "name": "First Steps",
            "description": "Complete your first lesson",
            "category": AchievementCategory.LEARNING,
            "rarity": AchievementRarity.COMMON,
            "icon": "🎯",
            "coin_reward": 50,
            "unlock_condition": {"type": "lesson_complete_count", "count": 1},
            "is_hidden": False,
            "display_order": 1,
        },
        {
            "name": "Quiz Taker",
            "description": "Complete your first quiz",
            "category": AchievementCategory.LEARNING,
            "rarity": AchievementRarity.COMMON,
            "icon": "📝",
            "coin_reward": 75,
            "unlock_condition": {"type": "quiz_complete_count", "count": 1},
            "is_hidden": False,
            "display_order": 2,
        },
        {
            "name": "Course Completer",
            "description": "Finish your first course",
            "category": AchievementCategory.LEARNING,
            "rarity": AchievementRarity.RARE,
            "icon": "🎓",
            "coin_reward": 500,
            "unlock_condition": {"type": "course_complete_count", "count": 1},
            "is_hidden": False,
            "display_order": 3,
        },
        {
            "name": "Curious Mind",
            "description": "Enroll in 10 different courses",
            "category": AchievementCategory.EXPLORER,
            "rarity": AchievementRarity.RARE,
            "icon": "🧠",
            "coin_reward": 250,
            "unlock_condition": {"type": "enrollment_count", "count": 10},
            "is_hidden": False,
            "display_order": 4,
        },
        # Mastery Category
        {
            "name": "Perfect Score",
            "description": "Get 100% on a quiz",
            "category": AchievementCategory.MASTERY,
            "rarity": AchievementRarity.RARE,
            "icon": "⭐",
            "coin_reward": 150,
            "unlock_condition": {"type": "perfect_quiz_count", "count": 1},
            "is_hidden": False,
            "display_order": 5,
        },
        {
            "name": "Ace Student",
            "description": "Get 100% on 5 different quizzes",
            "category": AchievementCategory.MASTERY,
            "rarity": AchievementRarity.EPIC,
            "icon": "🌟",
            "coin_reward": 750,
            "unlock_condition": {"type": "perfect_quiz_count", "count": 5},
            "is_hidden": False,
            "display_order": 6,
        },
        {
            "name": "Assignment Ace",
            "description": "Get A grade on 5 assignments",
            "category": AchievementCategory.MASTERY,
            "rarity": AchievementRarity.EPIC,
            "icon": "📚",
            "coin_reward": 500,
            "unlock_condition": {"type": "assignment_a_grade_count", "count": 5},
            "is_hidden": False,
            "display_order": 7,
        },
        # Social Category
        {
            "name": "Social Butterfly",
            "description": "Write 10 course reviews",
            "category": AchievementCategory.SOCIAL,
            "rarity": AchievementRarity.RARE,
            "icon": "🦋",
            "coin_reward": 200,
            "unlock_condition": {"type": "review_write_count", "count": 10},
            "is_hidden": False,
            "display_order": 8,
        },
        {
            "name": "Discussion Starter",
            "description": "Create 5 discussion threads",
            "category": AchievementCategory.SOCIAL,
            "rarity": AchievementRarity.COMMON,
            "icon": "💬",
            "coin_reward": 150,
            "unlock_condition": {"type": "discussion_thread_count", "count": 5},
            "is_hidden": False,
            "display_order": 9,
        },
        {
            "name": "Helpful Hand",
            "description": "Get 25 helpful votes on your posts",
            "category": AchievementCategory.SOCIAL,
            "rarity": AchievementRarity.EPIC,
            "icon": "🤝",
            "coin_reward": 300,
            "unlock_condition": {"type": "helpful_votes_count", "count": 25},
            "is_hidden": False,
            "display_order": 10,
        },
        # Streak Category
        {
            "name": "Streak Starter",
            "description": "Maintain a 3-day learning streak",
            "category": AchievementCategory.STREAK,
            "rarity": AchievementRarity.COMMON,
            "icon": "🔥",
            "coin_reward": 100,
            "unlock_condition": {"type": "streak_days", "days": 3},
            "is_hidden": False,
            "display_order": 11,
        },
        {
            "name": "Streak Champion",
            "description": "Maintain a 7-day learning streak",
            "category": AchievementCategory.STREAK,
            "rarity": AchievementRarity.RARE,
            "icon": "🔥🔥",
            "coin_reward": 200,
            "unlock_condition": {"type": "streak_days", "days": 7},
            "is_hidden": False,
            "display_order": 12,
        },
        {
            "name": "Streak Legend",
            "description": "Maintain a 30-day learning streak",
            "category": AchievementCategory.STREAK,
            "rarity": AchievementRarity.LEGENDARY,
            "icon": "🔥🔥🔥",
            "coin_reward": 1000,
            "unlock_condition": {"type": "streak_days", "days": 30},
            "is_hidden": False,
            "display_order": 13,
        },
        # Dedicated Category
        {
            "name": "Certificate Collector",
            "description": "Earn 3 course certificates",
            "category": AchievementCategory.DEDICATED,
            "rarity": AchievementRarity.EPIC,
            "icon": "🏆",
            "coin_reward": 750,
            "unlock_condition": {"type": "certificate_count", "count": 3},
            "is_hidden": False,
            "display_order": 14,
        },
        {
            "name": "Live Learner",
            "description": "Attend 5 live classes",
            "category": AchievementCategory.DEDICATED,
            "rarity": AchievementRarity.RARE,
            "icon": "📹",
            "coin_reward": 300,
            "unlock_condition": {"type": "live_class_attend_count", "count": 5},
            "is_hidden": False,
            "display_order": 15,
        },
        {
            "name": "Bookworm",
            "description": "Create 50 course notes",
            "category": AchievementCategory.DEDICATED,
            "rarity": AchievementRarity.RARE,
            "icon": "📖",
            "coin_reward": 200,
            "unlock_condition": {"type": "notes_create_count", "count": 50},
            "is_hidden": False,
            "display_order": 16,
        },
        # Special/Hidden Achievements
        {
            "name": "Early Bird",
            "description": "Complete a lesson before 8 AM",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.COMMON,
            "icon": "🌅",
            "coin_reward": 50,
            "unlock_condition": {"type": "lesson_before_hour", "hour": 8},
            "is_hidden": True,
            "display_order": 17,
        },
        {
            "name": "Night Owl",
            "description": "Complete a lesson after 10 PM",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.COMMON,
            "icon": "🦉",
            "coin_reward": 50,
            "unlock_condition": {"type": "lesson_after_hour", "hour": 22},
            "is_hidden": True,
            "display_order": 18,
        },
        {
            "name": "Weekend Warrior",
            "description": "Complete 3 lessons on a weekend",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.RARE,
            "icon": "⚔️",
            "coin_reward": 150,
            "unlock_condition": {"type": "weekend_lessons", "count": 3},
            "is_hidden": True,
            "display_order": 19,
        },
        {
            "name": "Platinum Learner",
            "description": "Earn 10,000 total coins",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.LEGENDARY,
            "icon": "💎",
            "coin_reward": 2000,
            "unlock_condition": {"type": "total_coins", "amount": 10000},
            "is_hidden": False,
            "display_order": 20,
        },
    ]


def check_and_unlock_achievement(
    db: Session, user: User, achievement: Achievement
) -> Optional[UserAchievement]:
    """
    Check if user meets conditions for an achievement and unlock it.

    Returns:
        UserAchievement if unlocked, None otherwise
    """
    # Check if already unlocked
    existing = (
        db.query(UserAchievement)
        .filter(
            and_(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement.id,
            )
        )
        .first()
    )

    if existing:
        return None  # Already unlocked

    # Check unlock condition
    condition = achievement.unlock_condition
    condition_type = condition.get("type")
    target_count = condition.get("count", 0)

    should_unlock = False

    try:
        if condition_type == "lesson_complete_count":
            # Count completed lessons
            from app.models.enrollment import Enrollment, EnrollmentStatus

            # This is an approximation - ideally we'd count completed lessons, not just enrollments
            # But for "First Steps" (1 lesson), checking if they have any progress is a start
            # Better: check completed enrollments or specific lesson progress if available
            # For now, let's assume if they have > 0 coins from lessons, they completed one
            # Or better, query Enrollment where status is completed
            completed_courses = (
                db.query(Enrollment)
                .filter(
                    Enrollment.user_id == user.id,
                    Enrollment.status == EnrollmentStatus.COMPLETED,
                )
                .count()
            )

            # If we want lesson granularity, we might need a LessonProgress model
            # For now, let's use a simpler proxy: if they have any completed course, they completed a lesson
            # OR check if they have any 'lesson_complete' coin transactions
            from app.models.coin_transaction import CoinTransaction

            lesson_completions = (
                db.query(CoinTransaction)
                .filter(
                    CoinTransaction.user_id == user.id,
                    CoinTransaction.reason == "lesson_complete",
                )
                .count()
            )

            if lesson_completions >= target_count:
                should_unlock = True

        elif condition_type == "quiz_complete_count":
            from app.models.quiz_attempt import QuizAttempt

            quiz_count = (
                db.query(QuizAttempt)
                .filter(
                    QuizAttempt.user_id == user.id, QuizAttempt.status == "completed"
                )
                .count()
            )
            if quiz_count >= target_count:
                should_unlock = True

        elif condition_type == "course_complete_count":
            from app.models.enrollment import Enrollment, EnrollmentStatus

            course_count = (
                db.query(Enrollment)
                .filter(
                    Enrollment.user_id == user.id,
                    Enrollment.status == EnrollmentStatus.COMPLETED,
                )
                .count()
            )
            if course_count >= target_count:
                should_unlock = True

        elif condition_type == "streak_days":
            target_days = condition.get("days", 0)
            if user.streak_days >= target_days:
                should_unlock = True

        elif condition_type == "total_coins":
            target_amount = condition.get("amount", 0)
            if user.coins >= target_amount:
                should_unlock = True

        # Add more condition types as needed

    except Exception as e:
        print(f"Error checking condition {condition_type}: {e}")
        return None

    if not should_unlock:
        return None

    # Create UserAchievement record
    user_achievement = UserAchievement(
        user_id=user.id,
        achievement_id=achievement.id,
        progress=100,  # 100% complete
        notified=False,
        unlocked_at=datetime.utcnow(),
    )

    db.add(user_achievement)

    # Award coins
    if achievement.coin_reward > 0:
        award_coins(
            db=db,
            user=user,
            amount=achievement.coin_reward,
            reason="achievement_unlock",
            description=f"Unlocked: {achievement.name}",
            reference_type="achievement",
            reference_id=achievement.id,
        )

    db.commit()
    db.refresh(user_achievement)

    return user_achievement


def check_achievements_for_trigger(
    db: Session, user: User, trigger_type: str, **context
) -> List[UserAchievement]:
    """
    Check and unlock any achievements triggered by an action.

    Args:
        db: Database session
        user: User performing action
        trigger_type: Type of action (e.g., "quiz_complete", "lesson_complete")
        **context: Additional context (score, etc.)

    Returns:
        List of newly unlocked achievements
    """
    newly_unlocked = []

    # Get all active achievements that match this trigger type
    # This is simplified - in practice, you'd have more sophisticated matching
    all_achievements = db.query(Achievement).filter(Achievement.is_active == True).all()

    for achievement in all_achievements:
        condition = achievement.unlock_condition
        condition_type = condition.get("type")

        # Map trigger types to condition types
        # This is where you'd implement the actual logic
        # For now, this is a placeholder

        try:
            unlocked = check_and_unlock_achievement(db, user, achievement)
            if unlocked:
                newly_unlocked.append(unlocked)
        except Exception as e:
            # Log but don't fail
            print(f"Error checking achievement {achievement.name}: {e}")
            continue

    return newly_unlocked


def get_user_achievements(db: Session, user_id: int) -> List[UserAchievement]:
    """Get all achievements unlocked by user"""
    return (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.unlocked_at.desc())
        .all()
    )


def get_achievement_progress(db: Session, user: User) -> dict:
    """Get user's progress toward all achievements"""
    all_achievements = db.query(Achievement).filter(Achievement.is_active == True).all()

    unlocked_ids = [ua.achievement_id for ua in user.achievements_earned]

    return {
        "total": len(all_achievements),
        "unlocked": len(unlocked_ids),
        "locked": len(all_achievements) - len(unlocked_ids),
        "completion_percentage": round(
            (len(unlocked_ids) / len(all_achievements)) * 100, 1
        )
        if all_achievements
        else 0,
    }
