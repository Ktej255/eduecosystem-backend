from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Any, Dict
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User
from app.models.meditation import MeditationSession, MeditationProgress

router = APIRouter()

@router.get("/analytics/batch", response_model=Dict[str, Any])
def get_batch_meditation_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Aggregate meditation performance for all students to detect focus trends.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # 1. Total minutes meditated by the whole student body
    total_seconds = db.query(func.sum(MeditationSession.duration_seconds)).filter(
        MeditationSession.created_at >= cutoff
    ).scalar() or 0
    
    # 2. Daily trend
    daily_stats = db.query(
        func.date(MeditationSession.created_at).label('date'),
        func.count(MeditationSession.id).label('sessions'),
        func.sum(MeditationSession.duration_seconds).label('seconds')
    ).filter(
        MeditationSession.created_at >= cutoff
    ).group_by(func.date(MeditationSession.created_at)).order_by('date').all()
    
    trend = [
        {
            "date": str(s.date),
            "sessions": s.sessions,
            "minutes": round(s.seconds / 60, 1)
        }
        for s in daily_stats
    ]
    
    # 3. Completion distribution (How many students at each level)
    level_dist = db.query(
        MeditationProgress.current_level,
        func.count(MeditationProgress.id)
    ).group_by(MeditationProgress.current_level).all()
    
    distribution = {f"Level {l}": count for l, count in level_dist}
    
    return {
        "total_minutes": round(total_seconds / 60, 1),
        "trend": trend,
        "level_distribution": distribution,
        "active_meditators_period": db.query(func.count(func.distinct(MeditationSession.user_id))).filter(
            MeditationSession.created_at >= cutoff
        ).scalar() or 0
    }

@router.post("/broadcast-nudge")
def broadcast_meditation_nudge(
    message: str,
    batch_name: str = "All",
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Sends a 'Focus Nudge' to all students currently on the platform.
    This acts as a 'Command' from the War Room.
    """
    from app.models.notifications import Notification
    
    # Get all active student IDs
    students = db.query(User.id).filter(User.role == "student", User.is_active == True).all()
    student_ids = [s.id for s in students]
    
    # Create notifications in bulk
    notifications = [
        Notification(
            user_id=sid,
            title="Focus Nudge from Admin",
            message=message,
            type="FOCUS_ALERT",
            is_read=False
        )
        for sid in student_ids
    ]
    
    db.add_all(notifications)
    db.commit()
    
    return {"status": "success", "recipients": len(student_ids)}
