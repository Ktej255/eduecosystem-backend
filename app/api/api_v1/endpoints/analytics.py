from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Dict
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service

router = APIRouter()

@router.get("/at-risk", response_model=List[Dict[str, Any]])
def get_at_risk_students(
    threshold: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get list of students at risk of dropping out or failing.
    Only accessible by Admins.
    """
    # Simple role check (in real app use permission dependency)
    # user role is string or enum
    is_admin = False
    if hasattr(current_user, "role"):
         if str(current_user.role).lower() == "admin":
             is_admin = True
    
    if not is_admin and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return analytics_service.get_at_risk_students(db, threshold)
