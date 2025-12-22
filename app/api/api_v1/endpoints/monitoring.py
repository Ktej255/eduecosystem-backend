from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.post("/exam/start")
def start_exam(
    exam_name: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Start a secure exam session.
    """
    from app.models.exam import ExamSession

    # Check if already in active session
    active_session = (
        db.query(ExamSession)
        .filter(ExamSession.user_id == current_user.id, ExamSession.is_active == True)
        .first()
    )

    if active_session:
        return {"msg": "Exam already in progress", "session_id": active_session.id}

    session = ExamSession(user_id=current_user.id, exam_name=exam_name)
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"msg": "Exam started", "session_id": session.id}


@router.post("/exam/violation")
def log_violation(
    session_id: int,
    violation_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log a violation (e.g., tab switch).
    """
    from app.models.exam import ExamSession

    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.violations += 1
    db.commit()

    return {"msg": "Violation logged", "total_violations": session.violations}


@router.post("/exam/end")
def end_exam(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    End the exam session.
    """
    from app.models.exam import ExamSession
    from datetime import datetime, timezone

    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    session.end_time = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()


@router.post("/attention")
def log_attention(
    focus_score: float,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log attention/focus score.
    """
    from app.models.activity_log import ActivityLog

    log = ActivityLog(
        user_id=current_user.id, action="attention_check", details=str(focus_score)
    )
    db.add(log)
    db.commit()

    return {"msg": "Attention logged"}


@router.get("/attention/stats")
def get_attention_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get attention statistics.
    """
    from app.models.activity_log import ActivityLog

    # Get average focus score from last 100 checks
    logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.action == "attention_check",
        )
        .order_by(ActivityLog.timestamp.desc())
        .limit(100)
        .all()
    )

    if not logs:
        return {"average_focus": 0, "total_checks": 0}

    scores = [float(log.details) for log in logs if log.details]
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "average_focus": round(avg_score, 2),
        "total_checks": len(logs),
        "recent_scores": scores[:10],
    }
