from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

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
        is_present=True
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[schemas.Attendance])
def read_attendance(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve attendance records.
    """
    if crud.user.is_superuser(current_user):
        return db.query(Attendance).offset(skip).limit(limit).all()
    else:
        return db.query(Attendance).filter(Attendance.user_id == current_user.id).offset(skip).limit(limit).all()
