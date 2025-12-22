from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func as sql_func

from app import models
from app.api import deps
from app.models.call_log import CallLog
from app.models.lead import Lead
from app.schemas.call_log import (
    CallLog as CallLogSchema,
    CallLogCreate,
    CallLogUpdate,
    QuickCallRequest,
    CallLogSummary,
)

router = APIRouter()


@router.post("/", response_model=CallLogSchema)
def create_call_log(
    *,
    db: Session = Depends(deps.get_db),
    call_data: CallLogCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log a phone call.
    """
    # Verify lead exists
    lead = db.query(Lead).filter(Lead.id == call_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    call_log = CallLog(
        user_id=current_user.id,
        lead_id=call_data.lead_id,
        call_type=call_data.call_type,
        phone_number=call_data.phone_number or lead.phone,
        duration_seconds=call_data.duration_seconds or 0,
        outcome=call_data.outcome,
        notes=call_data.notes,
        call_started_at=datetime.now()
    )
    
    # Update lead's last activity
    lead.last_activity = datetime.now()
    
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


@router.post("/quick-call", response_model=CallLogSchema)
def quick_call(
    *,
    db: Session = Depends(deps.get_db),
    call_request: QuickCallRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Initiate a quick call (logs the call start, user completes call on phone).
    """
    lead = db.query(Lead).filter(Lead.id == call_request.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    call_log = CallLog(
        user_id=current_user.id,
        lead_id=call_request.lead_id,
        call_type="OUTGOING",
        phone_number=call_request.phone_number,
        call_started_at=datetime.now()
    )
    
    lead.last_activity = datetime.now()
    
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


@router.put("/{id}", response_model=CallLogSchema)
def update_call_log(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    update_data: CallLogUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a call log (e.g., after call ends).
    """
    call_log = db.query(CallLog).filter(CallLog.id == id).first()
    
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    
    if call_log.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this call log")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(call_log, field, value)
    
    db.commit()
    db.refresh(call_log)
    return call_log


@router.get("/lead/{lead_id}", response_model=List[CallLogSchema])
def get_calls_for_lead(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get call history for a specific lead.
    """
    calls = db.query(CallLog).filter(
        CallLog.lead_id == lead_id
    ).order_by(CallLog.call_started_at.desc()).offset(skip).limit(limit).all()
    
    return calls


@router.get("/my-calls", response_model=List[CallLogSchema])
def get_my_calls(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    call_type: Optional[str] = None,
) -> Any:
    """
    Get current user's call history.
    """
    query = db.query(CallLog).filter(CallLog.user_id == current_user.id)
    
    if call_type:
        query = query.filter(CallLog.call_type == call_type)
    
    calls = query.order_by(CallLog.call_started_at.desc()).offset(skip).limit(limit).all()
    return calls


@router.get("/summary/{lead_id}", response_model=CallLogSummary)
def get_call_summary(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get call summary stats for a lead.
    """
    calls = db.query(CallLog).filter(CallLog.lead_id == lead_id).all()
    
    total_calls = len(calls)
    connected_calls = sum(1 for c in calls if c.outcome == "CONNECTED")
    missed_calls = sum(1 for c in calls if c.call_type == "MISSED" or c.outcome == "NO_ANSWER")
    
    total_duration = sum(c.duration_seconds or 0 for c in calls)
    total_duration_minutes = total_duration / 60
    avg_duration = total_duration / total_calls if total_calls > 0 else 0
    
    return CallLogSummary(
        total_calls=total_calls,
        connected_calls=connected_calls,
        missed_calls=missed_calls,
        total_duration_minutes=total_duration_minutes,
        average_duration_seconds=avg_duration
    )
