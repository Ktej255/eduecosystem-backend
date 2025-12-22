from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Enquiry])
def read_enquiries(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve enquiries.
    """
    enquiries = crud.enquiry.get_multi(db, skip=skip, limit=limit)
    return enquiries

@router.post("/", response_model=schemas.Enquiry)
def create_enquiry(
    *,
    db: Session = Depends(deps.get_db),
    enquiry_in: schemas.EnquiryCreate,
) -> Any:
    """
    Create new enquiry (public).
    """
    enquiry = crud.enquiry.create(db=db, obj_in=enquiry_in)
    return enquiry
