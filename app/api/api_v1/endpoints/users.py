from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.core.email import send_email
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import User, UserCreate

router = APIRouter()


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Create new user.
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud_user.create(db=db, obj_in=user_in)

    # Send welcome email
    background_tasks.add_task(
        send_email,
        email_to=user.email,
        subject="Welcome to Holistic Learning Ecosystem! 🌟",
        template_name="welcome.html",
        template_body={
            "name": user.full_name or "Learner",
            "dashboard_url": "http://localhost:3000/dashboard",
        },
    )

    return user


@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/", response_model=list[User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = crud_user.get_multi(db, skip=skip, limit=limit, role=role)
    return users
