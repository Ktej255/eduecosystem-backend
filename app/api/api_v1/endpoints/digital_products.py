from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.DigitalProduct])
def read_digital_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve digital products.
    """
    if crud.user.is_superuser(current_user):
        products = crud.digital_product.get_multi(db, skip=skip, limit=limit)
    else:
        products = crud.digital_product.get_by_instructor(
            db, instructor_id=current_user.id, skip=skip, limit=limit
        )
    return products

@router.post("/", response_model=schemas.DigitalProduct)
def create_digital_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: schemas.DigitalProductCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new digital product.
    """
    product = crud.digital_product.create_with_owner(
        db=db, obj_in=product_in, owner_id=current_user.id
    )
    return product
