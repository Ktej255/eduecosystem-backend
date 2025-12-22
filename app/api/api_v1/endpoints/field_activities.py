from typing import Any, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func as sql_func

from app import models
from app.api import deps
from app.models.field_activity import FieldActivity
from app.schemas.field_activity import (
    FieldActivity as FieldActivitySchema,
    FieldActivityCreate,
    FieldActivityUpdate,
    CheckInRequest,
    CheckOutRequest,
    MeetingLogRequest,
    FieldActivityDashboard,
)

router = APIRouter()


@router.post("/check-in", response_model=FieldActivitySchema)
def check_in(
    *,
    db: Session = Depends(deps.get_db),
    check_in_data: CheckInRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Record a check-in with location.
    """
    # Check if user already has an active check-in today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    active_check_in = db.query(FieldActivity).filter(
        and_(
            FieldActivity.user_id == current_user.id,
            FieldActivity.activity_type == "CHECK_IN",
            FieldActivity.started_at >= today_start,
            FieldActivity.ended_at == None
        )
    ).first()
    
    if active_check_in:
        raise HTTPException(
            status_code=400,
            detail="You already have an active check-in. Please check out first."
        )
    
    activity = FieldActivity(
        user_id=current_user.id,
        activity_type="CHECK_IN",
        latitude=check_in_data.latitude,
        longitude=check_in_data.longitude,
        address=check_in_data.address,
        notes=check_in_data.notes,
        started_at=datetime.now()
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.post("/check-out", response_model=FieldActivitySchema)
def check_out(
    *,
    db: Session = Depends(deps.get_db),
    check_out_data: CheckOutRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Record check-out and close the active check-in.
    """
    # Find active check-in
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    active_check_in = db.query(FieldActivity).filter(
        and_(
            FieldActivity.user_id == current_user.id,
            FieldActivity.activity_type == "CHECK_IN",
            FieldActivity.started_at >= today_start,
            FieldActivity.ended_at == None
        )
    ).first()
    
    if not active_check_in:
        raise HTTPException(
            status_code=400,
            detail="No active check-in found for today."
        )
    
    # Update the check-in with end info
    active_check_in.ended_at = datetime.now()
    if check_out_data.notes:
        active_check_in.notes = (active_check_in.notes or "") + f"\n[Check-out]: {check_out_data.notes}"
    if check_out_data.route_distance_km:
        active_check_in.route_distance_km = check_out_data.route_distance_km
    
    # Calculate duration
    duration = (active_check_in.ended_at - active_check_in.started_at).total_seconds() / 60
    active_check_in.duration_minutes = int(duration)
    
    db.commit()
    db.refresh(active_check_in)
    return active_check_in


@router.post("/meeting", response_model=FieldActivitySchema)
def log_meeting(
    *,
    db: Session = Depends(deps.get_db),
    meeting_data: MeetingLogRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log a meeting, visit, walk-in, or event.
    """
    valid_types = ["MEETING", "VISIT", "WALK_IN", "EVENT", "CAMPUS_VISIT"]
    if meeting_data.activity_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid activity type. Must be one of: {valid_types}"
        )
    
    activity = FieldActivity(
        user_id=current_user.id,
        activity_type=meeting_data.activity_type,
        latitude=meeting_data.latitude,
        longitude=meeting_data.longitude,
        address=meeting_data.address,
        lead_id=meeting_data.lead_id,
        title=meeting_data.title,
        notes=meeting_data.notes,
        duration_minutes=meeting_data.duration_minutes,
        photos=meeting_data.photos,
        started_at=datetime.now()
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/my-activities", response_model=List[FieldActivitySchema])
def get_my_activities(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
    activity_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Any:
    """
    Get current user's field activities.
    """
    query = db.query(FieldActivity).filter(FieldActivity.user_id == current_user.id)
    
    if activity_type:
        query = query.filter(FieldActivity.activity_type == activity_type)
    
    if date_from:
        query = query.filter(FieldActivity.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(FieldActivity.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    activities = query.order_by(FieldActivity.started_at.desc()).offset(skip).limit(limit).all()
    return activities


@router.get("/route/{user_id}/{date_str}", response_model=List[FieldActivitySchema])
def get_route_for_date(
    user_id: int,
    date_str: str,  # Format: YYYY-MM-DD
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get field activities (route) for a user on a specific date.
    Only admins can view other users' routes.
    """
    # Permission check
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' routes")
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    activities = db.query(FieldActivity).filter(
        and_(
            FieldActivity.user_id == user_id,
            FieldActivity.started_at >= start_of_day,
            FieldActivity.started_at <= end_of_day
        )
    ).order_by(FieldActivity.started_at.asc()).all()
    
    return activities


@router.get("/dashboard", response_model=FieldActivityDashboard)
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get field activity dashboard stats for current user.
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get today's activities
    today_activities = db.query(FieldActivity).filter(
        and_(
            FieldActivity.user_id == current_user.id,
            FieldActivity.started_at >= today_start
        )
    ).all()
    
    total_activities = len(today_activities)
    check_ins = sum(1 for a in today_activities if a.activity_type == "CHECK_IN")
    meetings = sum(1 for a in today_activities if a.activity_type in ["MEETING", "VISIT", "WALK_IN"])
    
    total_distance = sum(a.route_distance_km or 0 for a in today_activities)
    
    # Get active check-in
    active_check_in = next(
        (a for a in today_activities if a.activity_type == "CHECK_IN" and a.ended_at is None),
        None
    )
    
    return FieldActivityDashboard(
        total_activities_today=total_activities,
        check_ins_today=check_ins,
        meetings_today=meetings,
        total_distance_km=total_distance,
        active_check_in=active_check_in
    )


@router.put("/{id}", response_model=FieldActivitySchema)
def update_activity(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    update_data: FieldActivityUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a field activity.
    """
    activity = db.query(FieldActivity).filter(FieldActivity.id == id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    if activity.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this activity")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    return activity
