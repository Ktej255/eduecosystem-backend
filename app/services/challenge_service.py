"""
Challenge Service

Generates and manages daily/weekly challenges for user engagement.
Tracks progress and awards rewards on completion.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date, timedelta
from app.models.challenge import Challenge, UserChallenge, ChallengeType
from app.models.user import User
from app.services.coin_service import award_coins
from random import sample


def generate_daily_challenges(
    db: Session, target_date: Optional[date] = None
) -> List[Challenge]:
    """
    Generate 3 daily challenges for a given date.

    Args:
        db: Database session
        target_date: Date to generate challenges for (defaults to today)

    Returns:
        List of created Challenge objects
    """
    if target_date is None:
        target_date = date.today()

    # Check if challenges already exist for this date
    existing = (
        db.query(Challenge)
        .filter(
            Challenge.type == ChallengeType.DAILY, Challenge.start_date == target_date
        )
        .all()
    )

    if existing:
        return existing  # Already generated

    # Challenge templates - randomly select 3
    challenge_templates = [
        {
            "title": "Complete 2 Lessons",
            "description": "Finish any 2 lessons today",
            "requirement": {"type": "complete_lessons", "count": 2},
            "reward_coins": 30,
            "difficulty": 1,
        },
        {
            "title": "Take a Quiz",
            "description": "Complete any quiz with 70% or higher",
            "requirement": {"type": "quiz_score", "min_score": 70, "count": 1},
            "reward_coins": 40,
            "difficulty": 2,
        },
        {
            "title": "Discussion Participation",
            "description": "Write a discussion post or reply",
            "requirement": {"type": "discussion_posts", "count": 1},
            "reward_coins": 25,
            "difficulty": 1,
        },
        {
            "title": "Assignment Progress",
            "description": "Submit an assignment",
            "requirement": {"type": "assignment_submit", "count": 1},
            "reward_coins": 50,
            "difficulty": 3,
        },
        {
            "title": "Review Writer",
            "description": "Write a course review",
            "requirement": {"type": "review_write", "count": 1},
            "reward_coins": 30,
            "difficulty": 1,
        },
        {
            "title": "Study Session",
            "description": "Spend 30 minutes learning",
            "requirement": {"type": "time_spent", "minutes": 30},
            "reward_coins": 35,
            "difficulty": 2,
        },
    ]

    # Select 3 random challenges
    selected = sample(challenge_templates, min(3, len(challenge_templates)))

    challenges = []
    for template in selected:
        challenge = Challenge(
            title=template["title"],
            description=template["description"],
            type=ChallengeType.DAILY,
            start_date=target_date,
            end_date=target_date,  # Same day for daily challenges
            requirement=template["requirement"],
            reward_coins=template["reward_coins"],
            difficulty=template["difficulty"],
            is_active=True,
        )
        db.add(challenge)
        challenges.append(challenge)

    db.commit()
    for c in challenges:
        db.refresh(c)

    return challenges


def generate_weekly_challenges(
    db: Session, week_start: Optional[date] = None
) -> List[Challenge]:
    """
    Generate 2 weekly challenges for a given week.

    Args:
        db: Database session
        week_start: Monday of the target week (defaults to current week)

    Returns:
        List of created Challenge objects
    """
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

    week_end = week_start + timedelta(days=6)  # Sunday

    # Check if challenges already exist for this week
    existing = (
        db.query(Challenge)
        .filter(
            Challenge.type == ChallengeType.WEEKLY, Challenge.start_date == week_start
        )
        .all()
    )

    if existing:
        return existing

    # Weekly challenge templates
    challenge_templates = [
        {
            "title": "Complete 3 Courses",
            "description": "Finish 3 different courses this week",
            "requirement": {"type": "course_complete", "count": 3},
            "reward_coins": 500,
            "difficulty": 4,
        },
        {
            "title": "Quiz Master",
            "description": "Complete 5 quizzes with 80% or higher",
            "requirement": {"type": "quiz_high_score", "min_score": 80, "count": 5},
            "reward_coins": 300,
            "difficulty": 3,
        },
        {
            "title": "Streak Keeper",
            "description": "Maintain a 5-day learning streak",
            "requirement": {"type": "streak_maintain", "days": 5},
            "reward_coins": 250,
            "difficulty": 3,
        },
        {
            "title": "Social Learner",
            "description": "Post 10 discussion messages",
            "requirement": {"type": "discussion_posts", "count": 10},
            "reward_coins": 200,
            "difficulty": 2,
        },
        {
            "title": "Assignment Completer",
            "description": "Submit and get graded on 3 assignments",
            "requirement": {"type": "assignment_graded", "count": 3},
            "reward_coins": 400,
            "difficulty": 4,
        },
    ]

    # Select 2 random challenges
    selected = sample(challenge_templates, min(2, len(challenge_templates)))

    challenges = []
    for template in selected:
        challenge = Challenge(
            title=template["title"],
            description=template["description"],
            type=ChallengeType.WEEKLY,
            start_date=week_start,
            end_date=week_end,
            requirement=template["requirement"],
            reward_coins=template["reward_coins"],
            difficulty=template["difficulty"],
            is_active=True,
        )
        db.add(challenge)
        challenges.append(challenge)

    db.commit()
    for c in challenges:
        db.refresh(c)

    return challenges


def get_active_challenges_for_user(db: Session, user: User) -> dict:
    """
    Get all active challenges for a user with their progress.
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Generate challenges if they don't exist
    daily_challenges = generate_daily_challenges(db, today)
    weekly_challenges = generate_weekly_challenges(db, week_start)

    # Get or create UserChallenge records
    result = {"daily": [], "weekly": []}

    for challenge in daily_challenges:
        user_challenge = (
            db.query(UserChallenge)
            .filter(
                UserChallenge.user_id == user.id,
                UserChallenge.challenge_id == challenge.id,
            )
            .first()
        )

        if not user_challenge:
            user_challenge = UserChallenge(
                user_id=user.id,
                challenge_id=challenge.id,
                progress_data={},
                progress_percentage=0,
            )
            db.add(user_challenge)
            db.commit()
            db.refresh(user_challenge)

        result["daily"].append({"challenge": challenge, "progress": user_challenge})

    for challenge in weekly_challenges:
        user_challenge = (
            db.query(UserChallenge)
            .filter(
                UserChallenge.user_id == user.id,
                UserChallenge.challenge_id == challenge.id,
            )
            .first()
        )

        if not user_challenge:
            user_challenge = UserChallenge(
                user_id=user.id,
                challenge_id=challenge.id,
                progress_data={},
                progress_percentage=0,
            )
            db.add(user_challenge)
            db.commit()
            db.refresh(user_challenge)

        result["weekly"].append({"challenge": challenge, "progress": user_challenge})

    return result


def update_challenge_progress(
    db: Session, user: User, action_type: str, **context
) -> List[UserChallenge]:
    """
    Update user's progress on relevant challenges based on action.

    Returns:
        List of UserChallenge records that were updated
    """
    updated = []

    # Get active challenges for user
    active = get_active_challenges_for_user(db, user)

    all_user_challenges = []
    for item in active["daily"]:
        all_user_challenges.append(item["progress"])
    for item in active["weekly"]:
        all_user_challenges.append(item["progress"])

    # Update progress for matching challenges
    for user_challenge in all_user_challenges:
        if user_challenge.completed_at:
            continue  # Already completed

        challenge = user_challenge.challenge
        req = challenge.requirement
        req_type = req.get("type")

        # Check if this action matches the requirement
        if req_type == action_type or (
            req_type in ["quiz_score", "quiz_high_score"]
            and action_type == "quiz_complete"
        ):
            # Update progress
            # This is simplified - in practice, you'd track actual counts
            user_challenge.progress_percentage = min(
                100, user_challenge.progress_percentage + 33
            )

            if user_challenge.progress_percentage >= 100:
                user_challenge.completed_at = db.query(func.now()).scalar()

            db.commit()
            updated.append(user_challenge)

    return updated


def claim_challenge_reward(
    db: Session, user: User, user_challenge_id: int
) -> Optional[dict]:
    """
    Claim rewards for a completed challenge.

    Returns:
        Dict with reward info if successful, None otherwise
    """
    user_challenge = (
        db.query(UserChallenge)
        .filter(UserChallenge.id == user_challenge_id, UserChallenge.user_id == user.id)
        .first()
    )

    if not user_challenge:
        return None

    if user_challenge.reward_claimed:
        return None  # Already claimed

    if not user_challenge.completed_at:
        return None  # Not completed

    challenge = user_challenge.challenge

    # Award coins
    if challenge.reward_coins > 0:
        award_coins(
            db=db,
            user=user,
            amount=challenge.reward_coins,
            reason="challenge_complete",
            description=f"Completed: {challenge.title}",
            reference_type="challenge",
            reference_id=challenge.id,
        )

    # Mark as claimed
    user_challenge.reward_claimed = True
    user_challenge.claimed_at = db.query(func.now()).scalar()
    db.commit()

    result = {
        "coins_awarded": challenge.reward_coins,
        "challenge_title": challenge.title,
    }

    # Check for achievement reward
    if challenge.reward_achievement_id:
        result["achievement_unlocked"] = True

    return result
