from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List

from app.api import deps
from app.models.nudge import StudentNudgeWorkflow, NudgeHistory
from app.models.user import User

router = APIRouter()

@router.get("/workflows", response_model=List[dict])
def get_nudge_workflows(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """Get all smart nudge workflows."""
    workflows = db.query(StudentNudgeWorkflow).all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "trigger_type": w.trigger_type,
            "is_active": w.is_active,
            "action_type": w.action_type,
            "reward_amount": w.reward_amount,
            "created_at": w.created_at.isoformat()
        }
        for w in workflows
    ]

@router.post("/workflows", response_model=dict)
def create_nudge_workflow(
    name: str,
    trigger_type: str,
    message_template: str,
    trigger_config: dict = {},
    action_type: str = "PUSH",
    reward_amount: int = 0,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """Create a new nudge rule."""
    workflow = StudentNudgeWorkflow(
        name=name,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        message_template=message_template,
        action_type=action_type,
        reward_amount=reward_amount
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return {"status": "success", "id": workflow.id}

@router.get("/history", response_model=List[dict])
def get_nudge_history(
    limit: int = Query(100),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """Get history of execution of nudges."""
    history = db.query(NudgeHistory).order_by(NudgeHistory.sent_at.desc()).limit(limit).all()
    return [
        {
            "id": h.id,
            "user_email": h.user.email,
            "workflow_name": h.workflow.name,
            "sent_at": h.sent_at.isoformat(),
            "action": h.action_taken
        }
        for h in history
    ]

@router.post("/run-evaluation")
async def run_nudge_evaluation(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """Manually trigger a nudge evaluation cycle."""
    from app.services.nudge_service import nudge_service
    nudge_service.evaluate_rules(db)
    return {"status": "success", "message": "Nudge evaluation triggered"}
