from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import task as crud_task
from app.schemas.task import Task, TaskCreate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Task])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve tasks.
    """
    tasks = crud_task.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return tasks


@router.post("/", response_model=Task)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new task.
    """
    task = crud_task.create_with_owner(db=db, obj_in=task_in, user_id=current_user.id)
    return task


@router.post("/reschedule")
def reschedule_tasks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Smart Reschedule: Move incomplete tasks to peak productivity hours.
    """
    from app.models.activity_log import ActivityLog
    from datetime import datetime, timedelta

    # 1. Find Peak Hour (Reuse logic from analytics or import service)
    # For simplicity, let's do a quick query here or default to 10 AM
    logs = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id).all()
    peak_hour = 10  # Default
    if logs:
        hour_counts = {}
        for log in logs:
            h = log.timestamp.hour
            hour_counts[h] = hour_counts.get(h, 0) + 1
        peak_hour = max(hour_counts, key=hour_counts.get)

    # 2. Get incomplete tasks
    tasks = crud_task.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=0, limit=100
    )
    incomplete_tasks = [t for t in tasks if not t.is_completed]

    if not incomplete_tasks:
        return {"msg": "No tasks to reschedule"}

    # 3. Reschedule them to tomorrow starting at peak hour
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    current_time = datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, peak_hour, 0, 0
    )

    count = 0
    for task in incomplete_tasks:
        # Update task scheduled_date
        # Note: In a real app, we'd check for conflicts.
        task.scheduled_date = current_time
        current_time += timedelta(minutes=task.duration_minutes or 30)
        count += 1

    db.commit()

    return {"msg": f"Rescheduled {count} tasks to start at {peak_hour}:00 tomorrow."}
