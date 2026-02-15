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
    Get detailed analytics charts — computed from real progress data.
    """
    from app.models.universal_progress import UniversalProgress
    import json
    
    # Try to load real mastery from the user's synced state blob
    record = db.query(UniversalProgress).filter(
        UniversalProgress.user_id == current_user.id
    ).first()
    
    skills = []
    if record and record.state_blob:
        try:
            blob = json.loads(record.state_blob) if isinstance(record.state_blob, str) else record.state_blob
            progress = blob.get("progress", blob)
            mastery = progress.get("subjectMastery", {})
            
            subject_map = {
                "economy": "Economy",
                "polity": "Polity",
                "history": "History",
                "geography": "Geography",
                "science": "Science",
                "ethics": "Ethics",
                "security": "Security",
                "art_culture": "Art & Culture"
            }
            
            for key, label in subject_map.items():
                skills.append({
                    "subject": label,
                    "A": mastery.get(key, 0),
                    "fullMark": 100
                })
        except Exception:
            pass
    
    # Fallback if no real data
    if not skills:
        skills = [
            {"subject": "History", "A": 0, "fullMark": 100},
            {"subject": "Geography", "A": 0, "fullMark": 100},
            {"subject": "Polity", "A": 0, "fullMark": 100},
            {"subject": "Economy", "A": 0, "fullMark": 100},
            {"subject": "Science", "A": 0, "fullMark": 100},
        ]
    
    # Compute comparative from all users
    all_records = db.query(UniversalProgress).limit(100).all()
    global_scores = []
    for r in all_records:
        try:
            b = json.loads(r.state_blob) if isinstance(r.state_blob, str) else r.state_blob
            p = b.get("progress", b)
            m = p.get("subjectMastery", {})
            vals = [v for v in m.values() if isinstance(v, (int, float))]
            if vals:
                global_scores.append(sum(vals) / len(vals))
        except Exception:
            pass
    
    user_avg = sum(s["A"] for s in skills) / len(skills) if skills else 0
    global_avg = sum(global_scores) / len(global_scores) if global_scores else 0
    percentile = sum(1 for s in global_scores if s <= user_avg) / len(global_scores) * 100 if global_scores else 50
    
    comparative = {
        "user_focus": round(user_avg, 1),
        "global_focus": round(global_avg, 1),
        "user_percentile": round(percentile)
    }
    
    return {
        "skills": skills,
        "heatmap": [],
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

from app.schemas.analytics import EventCreate, EventResponse

@router.post("/events", response_model=EventResponse)
def create_analytics_event(
    *,
    db: Session = Depends(get_db),
    event_in: EventCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Log a new analytics event (e.g. behavioral signals).
    """
    return analytics_service.create_event(db, event_in, current_user.id)

@router.get("/focus-correlation", response_model=List[Dict[str, Any]])
def get_focus_correlation(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get correlation data between meditation focus and lesson completions.
    """
    return analytics_service.get_focus_correlation(db, current_user.id, days)

@router.get("/admin-overview", response_model=Dict[str, Any])
def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get aggregated admin/teacher analytics overview stats.
    """
    return analytics_service.get_admin_overview(db)
