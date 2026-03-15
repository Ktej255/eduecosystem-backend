from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import crud, models, schemas
from app.api import deps
from app.models.attendance import Attendance

router = APIRouter()

@router.post("/", response_model=schemas.Attendance)
def create_attendance(
    *,
    db: Session = Depends(deps.get_db),
    attendance_in: schemas.AttendanceCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Record attendance for a session.
    """
    timestamp = attendance_in.timestamp or datetime.utcnow()
    
    db_obj = Attendance(
        user_id=current_user.id,
        session_type=attendance_in.session_type,
        timestamp=timestamp,
        mode=attendance_in.mode,
        duration_minutes=attendance_in.duration_minutes or 0,
        is_late=attendance_in.is_late or False,
        is_present=True
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/admin/analytics")
def get_attendance_analytics(
    db: Session = Depends(deps.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get attendance analytics for admin dashboard.
    """
    from datetime import datetime, timedelta
    from app.models.user import User
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    
    total_today = db.query(Attendance).filter(Attendance.timestamp >= today_start).count()
    total_this_week = db.query(Attendance).filter(Attendance.timestamp >= week_start).count()
    
    on_time_today = db.query(Attendance).filter(
        Attendance.timestamp >= today_start,
        Attendance.is_late == False
    ).count()
    on_time_rate = round((on_time_today / total_today * 100), 1) if total_today > 0 else 0
    
    # Simple average for now
    total_all_time = db.query(Attendance).count()
    first_record = db.query(Attendance).order_by(Attendance.timestamp.asc()).first()
    if first_record:
        days_diff = (now - first_record.timestamp).days + 1
        average_daily = round(total_all_time / days_diff, 1)
    else:
        average_daily = 0
        
    # Streak leaders from User model
    streak_leaders = db.query(User).order_by(User.streak_days.desc()).limit(5).all()
    streak_data = [{"user_name": u.full_name or u.email, "streak": u.streak_days} for u in streak_leaders]
    
    return {
        "total_today": total_today,
        "total_this_week": total_this_week,
        "average_daily": average_daily,
        "on_time_rate": on_time_rate,
        "streak_leaders": streak_data
    }

@router.get("/admin/records")
def get_all_attendance_records(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 50,
    current_admin: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get all attendance records with user details.
    """
    from app.models.user import User
    
    total = db.query(Attendance).count()
    items = db.query(Attendance).order_by(Attendance.timestamp.desc()).offset(skip).limit(limit).all()
    
    records = []
    for item in items:
        user = db.query(User).filter(User.id == item.user_id).first()
        record = {
            "id": item.id,
            "user_id": item.user_id,
            "user_name": user.full_name if user else "Unknown",
            "session_date": item.timestamp.strftime("%Y-%m-%d"),
            "joined_at": item.timestamp.isoformat(),
            "duration_minutes": item.duration_minutes,
            "is_late": item.is_late,
            "status": "LATE" if item.is_late else "PRESENT",
            "user": {
                "id": user.id,
                "full_name": user.full_name or "Unknown",
                "email": user.email
            } if user else None
        }
        records.append(record)
        
    return {"records": records, "total": total}

@router.get("/admin/date/{date}")
def get_attendance_by_date(
    date: str,
    db: Session = Depends(deps.get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get attendance records for a specific date.
    """
    from datetime import datetime
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        next_day = date_obj + timedelta(days=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
    items = db.query(Attendance).filter(
        Attendance.timestamp >= date_obj,
        Attendance.timestamp < next_day
    ).all()
    
    return items

@router.get("/", response_model=List[schemas.Attendance])
def read_attendance(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve attendance records for the current user.
    """
    if crud.user.is_superuser(current_user):
        return db.query(Attendance).offset(skip).limit(limit).all()
    else:
        return db.query(Attendance).filter(Attendance.user_id == current_user.id).offset(skip).limit(limit).all()
