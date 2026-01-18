from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.recommendation_engine import recommendation_engine

router = APIRouter()

@router.get("/smart-bundle", response_model=Optional[Dict[str, Any]])
def get_smart_offer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a personalized smart bundle offer for the current user.
    """
    return recommendation_engine.generate_smart_offer(db, current_user.id)
