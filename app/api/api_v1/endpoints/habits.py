"""
Habit Tracking API Endpoints
Manage habits, track completions, award coins for consistency.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, date
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


# ============ SCHEMAS ============

class HabitTemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    icon: str
    recommended_time: Optional[str]
    duration_minutes: int
    coins_per_completion: int
    difficulty: str


class UserHabitOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: str
    category: str
    current_streak: int
    longest_streak: int
    total_completions: int
    coins_per_completion: int
    total_coins_earned: int
    is_completed_today: bool
    reminder_time: Optional[str]


class HabitCreate(BaseModel):
    template_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    icon: str = "✨"
    category: str = "custom"
    reminder_time: Optional[str] = None


class HabitCompletionResponse(BaseModel):
    success: bool
    already_completed: bool
    coins_earned: int
    streak_bonus: bool
    new_streak: int
    message: str


# ============ ENDPOINTS ============

@router.get("/templates", response_model=List[HabitTemplateOut])
async def get_habit_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get all available habit templates"""
    from app.models.habit import HabitTemplate
    
    query = db.query(HabitTemplate).filter(HabitTemplate.is_active == True)
    if category:
        query = query.filter(HabitTemplate.category == category)
    
    templates = query.all()
    
    return [
        HabitTemplateOut(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            icon=t.icon,
            recommended_time=t.recommended_time,
            duration_minutes=t.duration_minutes,
            coins_per_completion=t.coins_per_completion,
            difficulty=t.difficulty
        )
        for t in templates
    ]


@router.get("/my-habits", response_model=List[UserHabitOut])
async def get_my_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get user's active habits"""
    from app.models.habit import UserHabit
    
    habits = db.query(UserHabit).filter(
        UserHabit.user_id == current_user.id,
        UserHabit.is_active == True
    ).all()
    
    today = date.today()
    
    return [
        UserHabitOut(
            id=h.id,
            name=h.name,
            description=h.description,
            icon=h.icon,
            category=h.category,
            current_streak=h.current_streak,
            longest_streak=h.longest_streak,
            total_completions=h.total_completions,
            coins_per_completion=h.coins_per_completion,
            total_coins_earned=h.total_coins_earned,
            is_completed_today=h.last_completed_date == today,
            reminder_time=h.reminder_time
        )
        for h in habits
    ]


@router.post("/add-habit")
async def add_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Add a new habit from template or custom"""
    from app.models.habit import UserHabit, HabitTemplate
    
    if habit.template_id:
        # From template
        template = db.query(HabitTemplate).filter(HabitTemplate.id == habit.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        new_habit = UserHabit(
            user_id=current_user.id,
            template_id=template.id,
            name=template.name,
            description=template.description,
            icon=template.icon,
            category=template.category,
            coins_per_completion=template.coins_per_completion,
            reminder_time=habit.reminder_time or template.recommended_time
        )
    else:
        # Custom habit
        if not habit.name:
            raise HTTPException(status_code=400, detail="Name required for custom habit")
        
        new_habit = UserHabit(
            user_id=current_user.id,
            name=habit.name,
            description=habit.description,
            icon=habit.icon,
            category=habit.category,
            coins_per_completion=5,  # Default for custom
            reminder_time=habit.reminder_time
        )
    
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    
    return {"success": True, "habit_id": new_habit.id, "message": f"Habit '{new_habit.name}' added!"}


@router.post("/complete/{habit_id}", response_model=HabitCompletionResponse)
async def complete_habit(
    habit_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Mark a habit as completed today"""
    from app.models.habit import UserHabit, HabitCompletion
    from app.models.coin_transaction import CoinTransaction, TransactionType
    
    habit = db.query(UserHabit).filter(
        UserHabit.id == habit_id,
        UserHabit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Complete the habit
    result = habit.complete_today()
    
    if result["already_completed"]:
        return HabitCompletionResponse(
            success=False,
            already_completed=True,
            coins_earned=0,
            streak_bonus=False,
            new_streak=result["new_streak"],
            message="Already completed today!"
        )
    
    # Log completion
    completion = HabitCompletion(
        user_id=current_user.id,
        habit_id=habit_id,
        completed_date=date.today(),
        notes=notes,
        coins_earned=result["coins_earned"],
        streak_at_completion=result["new_streak"]
    )
    db.add(completion)
    
    # Award coins
    current_user.coins += result["coins_earned"]
    
    # Log transaction
    transaction = CoinTransaction(
        user_id=current_user.id,
        amount=result["coins_earned"],
        type=TransactionType.EARNED,
        reason=f"habit_{habit.name.lower().replace(' ', '_')}",
        description=f"Completed habit: {habit.name} (Day {result['new_streak']})",
        reference_type="habit",
        reference_id=habit_id,
        balance_after=current_user.coins
    )
    db.add(transaction)
    
    db.commit()
    
    message = f"🎉 Day {result['new_streak']}!"
    if result["streak_bonus"]:
        message += f" Streak bonus: +{result['coins_earned']} coins!"
    
    return HabitCompletionResponse(
        success=True,
        already_completed=False,
        coins_earned=result["coins_earned"],
        streak_bonus=result["streak_bonus"],
        new_streak=result["new_streak"],
        message=message
    )


@router.delete("/{habit_id}")
async def remove_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Remove a habit"""
    from app.models.habit import UserHabit
    
    habit = db.query(UserHabit).filter(
        UserHabit.id == habit_id,
        UserHabit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    habit.is_active = False
    db.commit()
    
    return {"success": True, "message": f"Habit '{habit.name}' removed"}


@router.get("/today-summary")
async def get_today_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get today's habit completion summary"""
    from app.models.habit import UserHabit
    
    habits = db.query(UserHabit).filter(
        UserHabit.user_id == current_user.id,
        UserHabit.is_active == True
    ).all()
    
    today = date.today()
    completed = [h for h in habits if h.last_completed_date == today]
    pending = [h for h in habits if h.last_completed_date != today]
    
    return {
        "total_habits": len(habits),
        "completed": len(completed),
        "pending": len(pending),
        "completion_rate": len(completed) / len(habits) if habits else 0,
        "completed_habits": [{"id": h.id, "name": h.name, "icon": h.icon} for h in completed],
        "pending_habits": [{"id": h.id, "name": h.name, "icon": h.icon} for h in pending]
    }


@router.get("/stats")
async def get_habit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get overall habit statistics"""
    from app.models.habit import UserHabit, HabitCompletion
    from datetime import timedelta
    
    habits = db.query(UserHabit).filter(
        UserHabit.user_id == current_user.id,
        UserHabit.is_active == True
    ).all()
    
    # Last 30 days completions
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_completions = db.query(HabitCompletion).filter(
        HabitCompletion.user_id == current_user.id,
        HabitCompletion.completed_date >= thirty_days_ago
    ).count()
    
    total_coins = sum(h.total_coins_earned for h in habits)
    best_streak = max((h.longest_streak for h in habits), default=0)
    
    return {
        "active_habits": len(habits),
        "total_completions_all_time": sum(h.total_completions for h in habits),
        "completions_last_30_days": recent_completions,
        "total_coins_from_habits": total_coins,
        "best_streak_ever": best_streak,
        "categories": list(set(h.category for h in habits))
    }
