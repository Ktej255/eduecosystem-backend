from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.category import category as crud_category
from app.crud.category import tag as crud_tag
from app.schemas.category import Category, CategoryCreate, Tag, TagCreate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve categories.
    """
    categories = crud_category.get_multi(db, skip=skip, limit=limit)
    return categories


@router.post("/", response_model=Category)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new category.
    """
    category = crud_category.get_by_slug(db, slug=category_in.slug)
    if category:
        raise HTTPException(
            status_code=400,
            detail="The category with this slug already exists in the system.",
        )
    category = crud_category.create(db, obj_in=category_in.model_dump())
    return category


@router.get("/tags", response_model=List[Tag])
def read_tags(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve tags.
    """
    tags = crud_tag.get_multi(db, skip=skip, limit=limit)
    return tags


@router.post("/tags", response_model=Tag)
def create_tag(
    *,
    db: Session = Depends(deps.get_db),
    tag_in: TagCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new tag.
    """
    tag = crud_tag.create(db, obj_in=tag_in.model_dump())
    return tag
