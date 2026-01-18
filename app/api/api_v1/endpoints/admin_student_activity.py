from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any, List, Optional
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.study_session import StudySession

router = APIRouter()

@router.get("/{student_id}/timeline", response_model=List[dict])
def get_student_activity_timeline(
    student_id: int,
    days: int = Query(1, ge=1, le=30),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Returns a per-minute resolution activity timeline for a specific student.
    Aggregates ActivityLogs and StudySessions.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # 1. Fetch Activity Logs
    logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == student_id,
        ActivityLog.timestamp >= cutoff
    ).order_by(ActivityLog.timestamp.asc()).all()
    
    # 2. Fetch Study Sessions (Pomodoros)
    sessions = db.query(StudySession).filter(
        StudySession.user_id == student_id,
        StudySession.start_time >= cutoff
    ).all()
    
    # 3. Merge and format into timeline events
    timeline = []
    
    for log in logs:
        timeline.append({
            "type": "ACTION",
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "details": log.details,
            "category": "Interactivity"
        })
        
    for session in sessions:
        timeline.append({
            "type": "STUDY_SESSION",
            "timestamp": session.start_time.isoformat(),
            "end_timestamp": session.end_time.isoformat() if session.end_time else None,
            "duration": session.duration_seconds,
            "category": "Focus",
            "details": "Pomodoro Session"
        })
        
    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return timeline

@router.get("/overview-stats", response_model=dict)
def get_student_activity_overview(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Provides high-level activity stats for the entire student body."""
    # Count unique active students in last 24h
    day_ago = datetime.utcnow() - timedelta(hours=24)
    active_now = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
        ActivityLog.timestamp >= day_ago
    ).scalar() or 0
    
    total_pomodoros_24h = db.query(func.count(StudySession.id)).filter(
        StudySession.start_time >= day_ago
    ).scalar() or 0
    
    return {
        "active_students_24h": active_now,
        "total_pomodoros_24h": total_pomodoros_24h,
        "timestamp": datetime.utcnow().isoformat()
    }
