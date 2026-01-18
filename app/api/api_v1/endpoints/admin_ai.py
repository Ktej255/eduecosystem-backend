from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List

from app.api import deps
from app.models.user import User
from app.services.ai_planning_service import ai_planning_service
from app.models.development import DevelopmentLog

router = APIRouter()

@router.get("/plan", response_model=dict)
async def get_ai_development_plan(
    lookback: int = Query(15),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Generate a 7-day AI suggested development plan based on recent history.
    """
    plan = await ai_planning_service.generate_strategic_plan(db, lookback_days=lookback)
    if not plan:
        raise HTTPException(status_code=500, detail="AI failed to generate plan")
    return plan

@router.post("/log-development", response_model=dict)
def log_development_action(
    portal: str,
    feature: str,
    action: str,
    description: str,
    impact: str = "Medium",
    affected_files: List[str] = [],
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Manually log a manual development action for future AI planning analysis.
    """
    log = DevelopmentLog(
        portal_name=portal,
        feature_name=feature,
        action_type=action,
        description=description,
        impact_level=impact,
        files_affected=affected_files
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"status": "success", "id": log.id}

@router.get("/history", response_model=List[dict])
def get_development_history(
    limit: int = Query(20),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Retrieve recent development history logs."""
    logs = db.query(DevelopmentLog).order_by(DevelopmentLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "portal": l.portal_name,
            "feature": l.feature_name,
            "action": l.action_type,
            "description": l.description,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
