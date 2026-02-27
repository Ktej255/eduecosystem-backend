from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app import crud, models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.StudentReport)
def sync_student_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: schemas.StudentReportCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create or update a student report (idempotent by report_key).
    Matches based on report_key for the current user to safely update existing states like streaks or test scores.
    """
    existing_report = crud.student_report.get_by_report_key(
        db=db, user_id=current_user.id, report_key=report_in.report_key
    )
    if existing_report:
        # Update existing
        return crud.student_report.update(db=db, db_obj=existing_report, obj_in=report_in)
    
    # Create new
    return crud.student_report.create_with_owner(
        db=db, obj_in=report_in, owner_id=current_user.id
    )

@router.get("/", response_model=List[schemas.StudentReport])
def read_student_reports(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    report_type: str = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve user reports automatically scoped. Optionally filter by type.
    """
    if report_type:
        reports = crud.student_report.get_by_user_and_type(
            db=db, user_id=current_user.id, report_type=report_type, skip=skip, limit=limit
        )
    else:
        reports = crud.student_report.get_by_user(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
    return reports

@router.get("/{report_key}", response_model=schemas.StudentReport)
def read_report_by_key(
    report_key: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Fetch a specific student report by its custom idempotent key.
    """
    report = crud.student_report.get_by_report_key(
        db=db, user_id=current_user.id, report_key=report_key
    )
    if not report:
        raise HTTPException(status_code=404, detail="Student report not found")
    return report
