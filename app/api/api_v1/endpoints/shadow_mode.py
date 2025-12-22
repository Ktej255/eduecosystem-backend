from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from app.api import deps
from app.models.user import User
from app.models.shadow_mode import ShadowModeSession

router = APIRouter()

@router.post("/start")
def start_shadow_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    day_number: int = 1,
    total_goals: int = 3,
) -> Any:
    """
    Start a new shadow mode session.
    """
    # Check if there's already an active session
    active_session = db.query(ShadowModeSession).filter(
        ShadowModeSession.user_id == current_user.id,
        ShadowModeSession.is_active == True
    ).first()
    
    if active_session:
        return {"error": "You already have an active session", "session": jsonable_encoder(active_session)}
    
    # Create new session
    session = ShadowModeSession(
        user_id=current_user.id,
        day_number=day_number,
        total_goals=total_goals,
        start_time=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "message": f"Shadow mode day {day_number} started!",
        "session": {
            "id": session.id,
            "day_number": session.day_number,
            "start_time": session.start_time,
            "total_goals": session.total_goals
        }
    }

@router.post("/end")
def end_shadow_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    goals_completed: int = 0,
    focus_score: float = 0.0,
    notes: str = None,
) -> Any:
    """
    End the current shadow mode session.
    """
    session = db.query(ShadowModeSession).filter(
        ShadowModeSession.user_id == current_user.id,
        ShadowModeSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Calculate duration
    session.end_time = datetime.utcnow()
    duration = (session.end_time - session.start_time).total_seconds() / 60  # minutes
    session.duration_minutes = int(duration)
    session.goals_completed = goals_completed
    session.focus_score = focus_score
    session.notes = notes
    session.is_active = False
    
    db.commit()
    db.refresh(session)
    
    # Award coins based on performance
    completion_rate = goals_completed / session.total_goals if session.total_goals > 0 else 0
    coins_earned = int(completion_rate * 100 + focus_score * 50)
    current_user.coins += coins_earned
    db.commit()
    
    return {
        "message": "Session completed!",
        "session": {
            "id": session.id,
            "day_number": session.day_number,
            "duration_minutes": session.duration_minutes,
            "goals_completed": goals_completed,
            "total_goals": session.total_goals,
            "focus_score": focus_score,
            "coins_earned": coins_earned
        }
    }

@router.get("/progress")
def get_shadow_progress(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get 7-day shadow mode progress.
    """
    # Get sessions from last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    sessions = db.query(ShadowModeSession).filter(
        ShadowModeSession.user_id == current_user.id,
        ShadowModeSession.start_time >= seven_days_ago
    ).order_by(desc(ShadowModeSession.day_number)).all()
    
    # Check for active session
    active_session = db.query(ShadowModeSession).filter(
        ShadowModeSession.user_id == current_user.id,
        ShadowModeSession.is_active == True
    ).first()
    
    # Calculate stats
    completed_days = len([s for s in sessions if not s.is_active])
    total_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
    avg_focus_score = sum(s.focus_score for s in sessions if s.focus_score) / len(sessions) if sessions else 0
    
    return {
        "current_day": active_session.day_number if active_session else None,
        "completed_days": completed_days,
        "total_days": 7,
        "total_minutes": total_minutes,
        "avg_focus_score": round(avg_focus_score, 2),
        "sessions": [
            {
                "id": s.id,
                "day_number": s.day_number,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration_minutes": s.duration_minutes,
                "goals_completed": s.goals_completed,
                "total_goals": s.total_goals,
                "focus_score": s.focus_score,
                "is_active": s.is_active
            }
            for s in sessions
        ],
        "active_session": {
            "id": active_session.id,
            "day_number": active_session.day_number,
            "start_time": active_session.start_time,
            "total_goals": active_session.total_goals
        } if active_session else None
    }

@router.get("/current")
def get_current_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get currently active shadow mode session.
    """
    session = db.query(ShadowModeSession).filter(
        ShadowModeSession.user_id == current_user.id,
        ShadowModeSession.is_active == True
    ).first()
    
    if not session:
        return {"active": False, "session": None}
    
    # Calculate elapsed time
    elapsed = (datetime.utcnow() - session.start_time).total_seconds() / 60
    
    return {
        "active": True,
        "session": {
            "id": session.id,
            "day_number": session.day_number,
            "start_time": session.start_time,
            "elapsed_minutes": int(elapsed),
            "total_goals": session.total_goals,
            "goals_completed": session.goals_completed
        }
    }
