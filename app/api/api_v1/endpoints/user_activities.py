from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app import models
from app.api import deps
from app.models.activity_log import ActivityLog

router = APIRouter()

class ActivityLogCreate(BaseModel):
    action: str
    details: Optional[str] = None

class ActivityLogOut(BaseModel):
    id: int
    action: str
    details: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

@router.post("/log", response_model=ActivityLogOut)
def log_activity(
    activity_in: ActivityLogCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log a user activity (e.g. topic completion).
    """
    activity = ActivityLog(
        user_id=current_user.id,
        action=activity_in.action,
        details=activity_in.details,
        timestamp=datetime.utcnow()
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

@router.get("/history", response_model=List[ActivityLogOut])
def get_activity_history(
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user activity history.
    """
    query = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id)
    if action:
        query = query.filter(ActivityLog.action == action)
    
    return query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
