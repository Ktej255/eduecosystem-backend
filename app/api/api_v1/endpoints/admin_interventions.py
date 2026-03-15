from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from app.api import deps
from app.models.user import User
from app.models.notification import Notification # Assuming existing notification model

router = APIRouter()

class StudentMessageRequest(BaseModel):
    student_id: int
    message: str
    intervention_type: str # ENCOURAGEMENT | WARNING | GUIDANCE | URGENT
    action_required: bool

class TeacherMessageRequest(BaseModel):
    teacher_id: int
    message: str
    regarding_student_id: Optional[int] = None
    priority: str # HIGH | NORMAL | LOW

class BatchNudgeRequest(BaseModel):
    target: str # ALL | GEOGRAPHY | HISTORY | AT_RISK
    message: str
    nudge_type: str # STUDY_REMINDER | MOTIVATION | ANNOUNCEMENT

from app.models.notification import Notification, NotificationType, NotificationPriority

@router.post("/message-student")
def message_student(
    request: StudentMessageRequest,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Send an intervention notification to a student."""
    notification = Notification(
        user_id=request.student_id,
        type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=f"Admin Intervention: {request.intervention_type}",
        message=request.message,
        priority=NotificationPriority.HIGH if request.intervention_type == "URGENT" else NotificationPriority.NORMAL,
        data={"sender_id": current_admin.id, "action_required": request.action_required}
    )
    db.add(notification)
    db.commit()
    return {"status": "success", "message": "Intervention dispatched to student"}

@router.post("/message-teacher")
def message_teacher(
    request: TeacherMessageRequest,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Send an intervention instruction to a teacher."""
    notification = Notification(
        user_id=request.teacher_id,
        type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=f"Admin Instruction: Priority {request.priority}",
        message=request.message,
        priority=request.priority.lower(),
        data={"sender_id": current_admin.id, "regarding_student": request.regarding_student_id}
    )
    db.add(notification)
    db.commit()
    return {"status": "success", "message": "Instruction dispatched to teacher"}

@router.post("/batch-nudge")
def batch_nudge(
    request: BatchNudgeRequest,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Nudge a batch of students."""
    # Logic to find students in the batch and create notifications
    return {"status": "success", "message": f"Batch nudge for {request.target} queued."}

@router.get("/history", response_model=List[Dict[str, Any]])
def get_intervention_history(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """Retrieve history of admin-sent notifications."""
    notifications = db.query(Notification).filter(
        Notification.type == NotificationType.SYSTEM_ANNOUNCEMENT
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": n.id,
            "timestamp": n.created_at.isoformat(),
            "target": f"User #{n.user_id}",
            "type": n.priority,
            "message": n.message,
            "status": "SENT"
        }
        for n in notifications
    ]
