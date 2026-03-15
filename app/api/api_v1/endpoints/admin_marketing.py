from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Any, List
from app.api import deps
from app.models.user import User
from app.models.marketing_automation import MarketingWorkflow, WorkflowExecution, MessageLog

router = APIRouter()

@router.get("/workflows", response_model=List[dict])
def get_all_marketing_workflows(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get all marketing workflows across all teachers for admin oversight.
    """
    workflows = db.query(MarketingWorkflow).all()
    result = []
    for wf in workflows:
        # Get creator info
        creator = db.query(User).filter(User.id == wf.created_by).first()
        
        # Get active executions
        active_count = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.workflow_id == wf.id,
            WorkflowExecution.status == "RUNNING"
        ).scalar() or 0
        
        result.append({
            "id": wf.id,
            "name": wf.name,
            "status": wf.status,
            "creator": creator.full_name if creator else "System",
            "enrolled": wf.total_enrolled,
            "completed": wf.total_completed,
            "converted": wf.total_converted,
            "active_now": active_count,
            "created_at": wf.created_at.isoformat()
        })
    return result

@router.get("/stats", response_model=dict)
def get_global_marketing_stats(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Aggregate marketing stats for admin dashboard.
    """
    total_emails = db.query(func.count(MessageLog.id)).filter(MessageLog.channel == "EMAIL").scalar() or 0
    total_whatsapp = db.query(func.count(MessageLog.id)).filter(MessageLog.channel == "WHATSAPP").scalar() or 0
    
    return {
        "total_emails_sent": total_emails,
        "total_whatsapp_sent": total_whatsapp,
        "active_workflows": db.query(func.count(MarketingWorkflow.id)).filter(MarketingWorkflow.status == "ACTIVE").scalar() or 0
    }
