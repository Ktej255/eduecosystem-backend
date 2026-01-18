from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List

from app.api import deps
from app.services.security_service import security_service
from app.models.user import User

router = APIRouter()

@router.get("/alerts", response_model=List[dict])
def get_security_alerts(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
    limit: int = Query(50),
) -> Any:
    """
    Get all active security alerts (Ghost Logins).
    """
    alerts = security_service.get_active_alerts(db, limit=limit)
    return [
        {
            "id": a.id,
            "user_email": a.user.email,
            "user_name": a.user.full_name,
            "login_a": {"ip": a.login_a_ip, "time": a.login_a_time.isoformat()},
            "login_b": {"ip": a.login_b_ip, "time": a.login_b_time.isoformat()},
            "distance_km": a.estimated_distance_km,
            "time_diff_min": a.time_difference_minutes,
            "risk_score": a.risk_score,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]

@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    notes: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Resolve a security alert.
    """
    from app.models.security import GhostLoginAlert
    from datetime import datetime
    
    alert = db.query(GhostLoginAlert).filter(GhostLoginAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.admin_notes = notes
    db.commit()
    
    return {"status": "success", "message": "Alert resolved"}
