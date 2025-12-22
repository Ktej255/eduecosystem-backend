"""
AI Debug API Endpoints
Provides endpoints for the Teacher Portal to view AI operation logs
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.ai_debug_service import ai_debug_service

router = APIRouter()


@router.get("/sessions")
async def list_ai_sessions(
    limit: int = Query(50, le=100),
    operation_type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List recent AI analysis sessions.
    
    - **limit**: Maximum number of sessions to return (default 50, max 100)
    - **operation_type**: Filter by operation type (e.g., "drill_evaluation")
    
    Requires admin or teacher role.
    """
    # Check permissions (admin or teacher)
    if current_user.role not in ["admin", "teacher", "superadmin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can access AI debug logs"
        )
    
    sessions = ai_debug_service.get_recent_sessions(
        db=db,
        limit=limit,
        operation_type=operation_type
    )
    
    return {
        "total": len(sessions),
        "sessions": sessions
    }


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get step-by-step breakdown of an AI session.
    
    Returns all logged steps for the given session, ordered by step number.
    """
    # Check permissions
    if current_user.role not in ["admin", "teacher", "superadmin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can access AI debug logs"
        )
    
    steps = ai_debug_service.get_session_logs(db=db, session_id=session_id)
    
    if not steps:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or has no logs"
        )
    
    return {
        "session_id": session_id,
        "total_steps": len(steps),
        "steps": steps
    }


@router.get("/sessions/{session_id}/steps/{step_number}")
async def get_step_details(
    session_id: str,
    step_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed input/output for a specific step.
    
    Returns full (non-truncated) input and output data for the step.
    """
    # Check permissions
    if current_user.role not in ["admin", "teacher", "superadmin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can access AI debug logs"
        )
    
    step = ai_debug_service.get_step_details(
        db=db,
        session_id=session_id,
        step_number=step_number
    )
    
    if not step:
        raise HTTPException(
            status_code=404,
            detail=f"Step {step_number} not found in session {session_id}"
        )
    
    return step


@router.get("/stats")
async def get_ai_stats(
    days: int = Query(7, le=30),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get aggregate AI usage statistics.
    
    Returns summary statistics about AI operations over the specified period.
    """
    # Check permissions
    if current_user.role not in ["admin", "teacher", "superadmin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and teachers can access AI debug logs"
        )
    
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models.ai_debug_logs import AIDebugSession
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get aggregate stats
    stats = db.query(
        func.count(AIDebugSession.id).label("total_sessions"),
        func.sum(AIDebugSession.total_tokens).label("total_tokens"),
        func.sum(AIDebugSession.total_cost).label("total_cost"),
        func.avg(AIDebugSession.total_duration_ms).label("avg_duration_ms"),
        func.sum(func.cast(AIDebugSession.had_errors, type_=int)).label("error_count"),
        func.sum(func.cast(AIDebugSession.had_fallbacks, type_=int)).label("fallback_count")
    ).filter(
        AIDebugSession.created_at >= start_date
    ).first()
    
    # Get count by operation type
    by_type = db.query(
        AIDebugSession.operation_type,
        func.count(AIDebugSession.id).label("count")
    ).filter(
        AIDebugSession.created_at >= start_date
    ).group_by(AIDebugSession.operation_type).all()
    
    return {
        "period_days": days,
        "total_sessions": stats.total_sessions or 0,
        "total_tokens": stats.total_tokens or 0,
        "total_cost": round(stats.total_cost or 0, 4),
        "avg_duration_ms": round(stats.avg_duration_ms or 0, 2),
        "error_count": stats.error_count or 0,
        "fallback_count": stats.fallback_count or 0,
        "by_operation_type": [
            {"type": t.operation_type, "count": t.count}
            for t in by_type
        ]
    }
