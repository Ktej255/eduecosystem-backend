"""
Coin Service

Handles all coin-related operations including:
- Awarding coins for actions
- Recording transactions
- Checking balances
- Integration with achievement system
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.coin_transaction import CoinTransaction, TransactionType


# Coin reward amounts for various actions
COIN_REWARDS = {
    "lesson_complete": 10,
    "quiz_complete": 25,
    "quiz_perfect": 50,  # 100% score
    "quiz_high_score": 35,  # 90%+ score
    "assignment_submit": 30,
    "assignment_a_grade": 100,  # 90%+ grade
    "assignment_b_grade": 75,  # 80-89% grade
    "course_complete": 500,
    "certificate_earn": 250,
    "review_write": 20,
    "review_helpful": 5,  # When your review gets a helpful vote
    "discussion_post": 15,
    "discussion_reply": 10,
    "daily_login": 5,
    "streak_maintain": 10,  # Per day maintained
    "streak_milestone_7": 100,  # 7 day streak bonus
    "streak_milestone_30": 500,  # 30 day streak bonus
    "live_class_attend": 25,
}


def award_coins(
    db: Session,
    user: User,
    amount: int,
    reason: str,
    description: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
) -> CoinTransaction:
    """
    Award coins to a user and create transaction record.
    """
    # Update user's coin balance
    user.coins += amount

    # Create transaction record
    transaction = CoinTransaction(
        user_id=user.id,
        amount=amount,
        type=TransactionType.EARNED,
        reason=reason,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        balance_after=user.coins,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Wolf Packs: Sync points to user's pack(s)
    try:
        from app.services.pack_service import pack_service
        pack_service.sync_points_to_pack(db, user.id, amount)
    except Exception as pack_err:
        print(f"Error syncing points to pack: {pack_err}")

    return transaction


def spend_coins(
    db: Session,
    user: User,
    amount: int,
    reason: str,
    description: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
) -> Optional[CoinTransaction]:
    """
    Deduct coins from user (for purchases).
    """
    if user.coins < amount:
        return None

    # Update user's coin balance (negative for spending)
    user.coins -= amount

    # Create transaction record
    transaction = CoinTransaction(
        user_id=user.id,
        amount=-amount,  # Negative for spending
        type=TransactionType.SPENT,
        reason=reason,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        balance_after=user.coins,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def trigger_coin_reward(
    db: Session, user: User, action: str, **context
) -> Optional[CoinTransaction]:
    """
    Trigger coin reward for a specific action.
    """
    # Get reward amount for action
    amount = COIN_REWARDS.get(action, 0)

    if amount == 0:
        return None

    # Extract reference info from context
    reference_type = context.get("reference_type")
    reference_id = context.get("reference_id")
    description = context.get("description")

    # Award coins
    try:
        transaction = award_coins(
            db=db,
            user=user,
            amount=amount,
            reason=action,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )

        # Check for achievements triggered by this action
        try:
            from app.services.achievement_service import check_achievements_for_trigger

            check_achievements_for_trigger(
                db=db, user=user, trigger_type=action, **context
            )
        except Exception as ach_err:
            print(f"Error checking achievements: {ach_err}")

        return transaction

    except Exception as e:
        print(f"Error awarding coins: {e}")
        return None


def get_user_transaction_history(
    db: Session, user_id: int, limit: int = 50, skip: int = 0
) -> list[CoinTransaction]:
    """Get user's coin transaction history"""
    return (
        db.query(CoinTransaction)
        .filter(CoinTransaction.user_id == user_id)
        .order_by(CoinTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_earnings_summary(db: Session, user_id: int) -> dict:
    """Get summary of user's coin earnings by category"""
    transactions = (
        db.query(CoinTransaction)
        .filter(
            CoinTransaction.user_id == user_id,
            CoinTransaction.type == TransactionType.EARNED,
        )
        .all()
    )

    summary = {}
    total_earned = 0

    for trans in transactions:
        reason = trans.reason
        amount = trans.amount

        if reason not in summary:
            summary[reason] = {"count": 0, "total": 0}

        summary[reason]["count"] += 1
        summary[reason]["total"] += amount
        total_earned += amount

    return {"total_earned": total_earned, "breakdown": summary}


def check_daily_login_and_streak(db: Session, user: User) -> dict:
    """
    Check for daily login and update streak.
    """
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    today = now.date()

    # Initialize response
    result = {
        "daily_login_awarded": False,
        "streak_updated": False,
        "streak_days": user.streak_days,
        "coins_earned": 0,
    }

    # Check if this is the first login ever or first login today
    last_login_date = user.last_login.date() if user.last_login else None

    # If already logged in today, just update timestamp and return
    if last_login_date == today:
        user.last_login = now
        db.commit()
        return result

    # It's a new day!
    result["daily_login_awarded"] = True

    # Award daily login coins
    daily_tx = trigger_coin_reward(
        db=db, user=user, action="daily_login", description="Daily login bonus"
    )
    if daily_tx:
        result["coins_earned"] += daily_tx.amount

    # Check streak
    if last_login_date == today - timedelta(days=1):
        # Consecutive day! Increment streak
        user.streak_days += 1
        result["streak_updated"] = True

        # Award streak maintenance bonus
        streak_tx = trigger_coin_reward(
            db=db,
            user=user,
            action="streak_maintain",
            description=f"Maintained {user.streak_days}-day streak",
        )
        if streak_tx:
            result["coins_earned"] += streak_tx.amount

        # Check for milestones
        if user.streak_days == 7:
            milestone_tx = trigger_coin_reward(
                db=db,
                user=user,
                action="streak_milestone_7",
                description="7-day streak milestone!",
            )
            if milestone_tx:
                result["coins_earned"] += milestone_tx.amount

        elif user.streak_days == 30:
            milestone_tx = trigger_coin_reward(
                db=db,
                user=user,
                action="streak_milestone_30",
                description="30-day streak milestone!",
            )
            if milestone_tx:
                result["coins_earned"] += milestone_tx.amount

    else:
        # Streak broken or first login
        user.streak_days = 1
        result["streak_updated"] = True

    # Update last login
    user.last_login = now
    result["streak_days"] = user.streak_days

    db.commit()
    return result
