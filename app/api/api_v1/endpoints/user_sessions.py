from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app import crud, models, schemas
from app.api import deps
from app.models.user_session import UserActivitySession

router = APIRouter()

@router.post("/heartbeat", response_model=schemas.user_session.HeartbeatResponse)
def session_heartbeat(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    request: Request
) -> Any:
    """
    Update or create a user session heartbeat.
    Called by the frontend every 60s to track platform usage.
    """
    now = datetime.now(timezone.utc)
    
    # Check for an active session (last heartbeat within 5 minutes)
    five_mins_ago = now - timedelta(minutes=5)
    
    active_session = db.query(UserActivitySession).filter(
        UserActivitySession.user_id == current_user.id,
        UserActivitySession.is_active == True,
        UserActivitySession.last_heartbeat >= five_mins_ago
    ).order_by(UserActivitySession.last_heartbeat.desc()).first()
    
    if active_session:
        # Update existing session
        diff = (now - active_session.start_time).total_seconds()
        active_session.duration_seconds = int(diff)
        active_session.last_heartbeat = now
        db.add(active_session)
        db.commit()
        db.refresh(active_session)
        
        return {
            "session_id": active_session.id,
            "duration_seconds": active_session.duration_seconds,
            "status": "updated"
        }
    else:
        # Close any lingering "active" sessions that are stale
        db.query(UserActivitySession).filter(
            UserActivitySession.user_id == current_user.id,
            UserActivitySession.is_active == True
        ).update({"is_active": False, "end_time": now})
        
        # Start new session
        new_session = UserActivitySession(
            user_id=current_user.id,
            start_time=now,
            last_heartbeat=now,
            is_active=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return {
            "session_id": new_session.id,
            "duration_seconds": 0,
            "status": "created"
        }

@router.get("/me", response_model=List[schemas.user_session.UserSession])
def get_my_sessions(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's historical sessions.
    """
    return db.query(models.user_session.UserActivitySession).filter(models.user_session.UserActivitySession.user_id == current_user.id).order_by(models.user_session.UserActivitySession.start_time.desc()).limit(50).all()
