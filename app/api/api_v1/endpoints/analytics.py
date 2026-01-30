from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Dict
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.analytics_service import analytics_service

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get comprehensive analytics for user dashboard.
    """
    return analytics_service.get_dashboard_analytics(db, current_user.id)

@router.get("/detailed", response_model=Dict[str, Any])
def get_detailed_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get detailed analytics charts.
    """
    # Skills radar data
    skills = [
        {"subject": "History", "A": 75, "fullMark": 100},
        {"subject": "Geography", "A": 68, "fullMark": 100},
        {"subject": "Polity", "A": 82, "fullMark": 100},
        {"subject": "Economics", "A": 70, "fullMark": 100},
        {"subject": "Science", "A": 65, "fullMark": 100},
    ]
    
    # Heatmap data (placeholder - would be calculated from activity logs)
    heatmap = []
    
    # Comparative analysis
    comparative = {
        "user_focus": 75.5,
        "global_focus": 72.0,
        "user_percentile": 68
    }
    
    return {
        "skills": skills,
        "heatmap": heatmap,
        "comparative": comparative
    }

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
