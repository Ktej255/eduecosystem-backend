"""
Streak API Endpoints
Track daily engagement, award coins, and manage streak freeze tokens.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, date
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


# ============ SCHEMAS ============

class StreakStatus(BaseModel):
    current_streak: int
    longest_streak: int
    freeze_tokens: int
    total_active_days: int
    total_streak_coins: int
    last_activity_date: Optional[str]
    milestones: dict


class StreakUpdate(BaseModel):
    activity_type: str  # meditation, retention, graphotherapy


class StreakUpdateResponse(BaseModel):
    streak_continued: bool
    streak_broken: bool
    freeze_used: bool
    new_streak: int
    coins_earned: int
    milestone_reached: Optional[str]
    message: str


# ============ ENDPOINTS ============

@router.get("/status", response_model=StreakStatus)
async def get_streak_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get user's current streak status"""
    from app.models.streak import UserStreak
    
    streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    
    if not streak:
        # Create initial streak record
        streak = UserStreak(user_id=current_user.id)
        db.add(streak)
        db.commit()
        db.refresh(streak)
    
    return StreakStatus(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        freeze_tokens=streak.freeze_tokens,
        total_active_days=streak.total_active_days,
        total_streak_coins=streak.total_streak_coins,
        last_activity_date=str(streak.last_activity_date) if streak.last_activity_date else None,
        milestones={
            "7_day": streak.milestone_7_reached,
            "30_day": streak.milestone_30_reached,
            "100_day": streak.milestone_100_reached
        }
    )


@router.post("/log-activity", response_model=StreakUpdateResponse)
async def log_activity(
    activity: StreakUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Log an activity and update streak.
    Call this after completing meditation, retention review, or graphotherapy.
    """
    from app.models.streak import UserStreak, DailyActivity
    from app.models.coin_transaction import CoinTransaction, TransactionType
    
    # Get or create streak
    streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    if not streak:
        streak = UserStreak(user_id=current_user.id)
        db.add(streak)
        db.commit()
        db.refresh(streak)
    
    # Update streak
    now = datetime.now(timezone.utc)
    result = streak.check_and_update_streak(now)
    
    # Log daily activity
    today = date.today()
    daily = db.query(DailyActivity).filter(
        DailyActivity.user_id == current_user.id,
        DailyActivity.activity_date == today
    ).first()
    
    if not daily:
        daily = DailyActivity(user_id=current_user.id, activity_date=today)
        db.add(daily)
    
    # Mark activity type
    if activity.activity_type == "meditation":
        daily.meditation_completed = True
    elif activity.activity_type == "retention":
        daily.retention_completed = True
    elif activity.activity_type == "graphotherapy":
        daily.graphotherapy_completed = True
    
    # Award coins if earned
    if result["coins_earned"] > 0:
        # Update user balance
        current_user.coins += result["coins_earned"]
        daily.coins_earned += result["coins_earned"]
        
        # Log transaction
        reason = f"streak_day_{streak.current_streak}"
        if result["milestone_reached"]:
            reason = f"streak_milestone_{result['milestone_reached']}"
        
        transaction = CoinTransaction(
            user_id=current_user.id,
            amount=result["coins_earned"],
            type=TransactionType.EARNED,
            reason=reason,
            description=f"Streak reward: Day {streak.current_streak}",
            reference_type="streak",
            reference_id=streak.id,
            balance_after=current_user.coins
        )
        db.add(transaction)
    
    db.commit()
    
    return StreakUpdateResponse(**result)


@router.post("/use-freeze")
async def use_freeze_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Manually use a freeze token to protect streak"""
    from app.models.streak import UserStreak
    
    streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    
    if not streak or streak.freeze_tokens <= 0:
        raise HTTPException(status_code=400, detail="No freeze tokens available")
    
    streak.freeze_tokens -= 1
    db.commit()
    
    return {
        "success": True,
        "remaining_tokens": streak.freeze_tokens,
        "message": "❄️ Freeze token used! Your streak is protected for today."
    }


@router.get("/leaderboard")
async def get_streak_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get top streaks for motivation"""
    from app.models.streak import UserStreak
    
    top_streaks = db.query(UserStreak).order_by(
        UserStreak.current_streak.desc()
    ).limit(limit).all()
    
    # Get user's rank
    user_streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    user_rank = None
    if user_streak:
        higher_count = db.query(UserStreak).filter(
            UserStreak.current_streak > user_streak.current_streak
        ).count()
        user_rank = higher_count + 1
    
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "user_id": s.user_id,
                "streak": s.current_streak,
                "longest": s.longest_streak
            }
            for i, s in enumerate(top_streaks)
        ],
        "your_rank": user_rank,
        "your_streak": user_streak.current_streak if user_streak else 0
    }


@router.get("/calendar/{month}")
async def get_activity_calendar(
    month: int,
    year: int = 2024,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get activity calendar for visualization"""
    from app.models.streak import DailyActivity
    from datetime import date
    
    # Get all activities for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    activities = db.query(DailyActivity).filter(
        DailyActivity.user_id == current_user.id,
        DailyActivity.activity_date >= start_date,
        DailyActivity.activity_date < end_date
    ).all()
    
    calendar_data = {}
    for a in activities:
        day_str = str(a.activity_date)
        calendar_data[day_str] = {
            "meditation": a.meditation_completed,
            "retention": a.retention_completed,
            "graphotherapy": a.graphotherapy_completed,
            "coins": a.coins_earned
        }
    
    return {"month": month, "year": year, "activities": calendar_data}
