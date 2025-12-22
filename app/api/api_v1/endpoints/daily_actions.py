from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app import crud, models
from app.api import deps
from app.schemas.daily_action import (
    DailyActionSummary,
    DailyTaskCreate,
    DailyTaskUpdate,
    DailyTaskResponse,
    HabitCreate,
    HabitResponse,
    DailyReflectionCreate,
    DailyReflectionResponse
)

daily_router = APIRouter()
print("DEBUG: daily_router created in daily_actions.py")

@daily_router.get("/today", response_model=DailyActionSummary)
def get_daily_actions_today(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all daily actions for today (Tasks, Habits, Reflection).
    """
    today = date.today()
    
    # 1. Get Tasks
    tasks = db.query(models.DailyTask).filter(
        models.DailyTask.user_id == current_user.id,
        models.DailyTask.date == today
    ).all()
    
    # 2. Get Habits (Active)
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == True
    ).all()
    
    # Populate habit logs for the last 7 days (simplified for now, just today)
    habit_responses = []
    for habit in habits:
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id,
            models.HabitLog.date == today
        ).all()
        
        habit_response = HabitResponse.model_validate(habit)
        # Manually populate logs if needed, or rely on relationship if set up
        # For now, let's assume basic response
        habit_responses.append(habit_response)

    # 3. Get Reflection
    reflection = db.query(models.DailyReflection).filter(
        models.DailyReflection.user_id == current_user.id,
        models.DailyReflection.date == today
    ).first()
    
    # Stats (Placeholder)
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.completed])
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    return {
        "date": today,
        "tasks": tasks,
        "habits": habit_responses,
        "reflection": reflection,
        "tasks_completed": completed_tasks,
        "total_tasks": total_tasks,
        "streak_days": 0, # Placeholder
        "completion_rate": completion_rate
    }

@daily_router.post("/tasks", response_model=DailyTaskResponse)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: DailyTaskCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new daily task.
    """
    task = models.DailyTask(
        **task_in.model_dump(),
        user_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@daily_router.patch("/tasks/{task_id}", response_model=DailyTaskResponse)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: Any,
    task_update: DailyTaskUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a task (e.g. toggle completion).
    """
    task = db.query(models.DailyTask).filter(
        models.DailyTask.id == task_id,
        models.DailyTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
        
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@daily_router.post("/habits", response_model=HabitResponse)
def create_habit(
    *,
    db: Session = Depends(deps.get_db),
    habit_in: HabitCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new habit.
    """
    habit = models.Habit(
        **habit_in.model_dump(),
        user_id=current_user.id
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit

@daily_router.post("/habits/{habit_id}/toggle", response_model=Any)
def toggle_habit(
    *,
    db: Session = Depends(deps.get_db),
    habit_id: Any,
    date_in: date,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Toggle a habit for a specific date.
    """
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
        
    log = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id,
        models.HabitLog.date == date_in
    ).first()
    
    if log:
        # Toggle
        log.completed = not log.completed
    else:
        # Create
        log = models.HabitLog(
            habit_id=habit_id,
            date=date_in,
            completed=True
        )
        db.add(log)
        
    db.commit()
    return {"status": "success", "completed": log.completed}

@daily_router.post("/reflection", response_model=DailyReflectionResponse)
def create_reflection(
    *,
    db: Session = Depends(deps.get_db),
    reflection_in: DailyReflectionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Save daily reflection.
    """
    # Check if exists
    reflection = db.query(models.DailyReflection).filter(
        models.DailyReflection.user_id == current_user.id,
        models.DailyReflection.date == reflection_in.date
    ).first()
    
    if reflection:
        reflection.content = reflection_in.content
    else:
        reflection = models.DailyReflection(
            **reflection_in.model_dump(),
            user_id=current_user.id
        )
        db.add(reflection)
        
    db.commit()
    db.refresh(reflection)
    return reflection
