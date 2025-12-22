from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Asset])
def read_assets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    file_type: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve assets.
    """
    if crud.user.is_superuser(current_user):
        if file_type:
            assets = crud.asset.get_by_type(db, file_type=file_type, skip=skip, limit=limit)
        else:
            assets = crud.asset.get_multi(db, skip=skip, limit=limit)
    else:
        # Regular users only see their own assets
        # Note: You might want to allow instructors to see shared assets or similar
        # For now, let's restrict to own assets
        assets = crud.asset.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return assets
