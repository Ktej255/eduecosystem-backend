from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Any, List, Dict
from app.api import deps
from app.models.user import User
from app.models.lead import Lead
from app.models.meditation import MeditationProgress
from app.models.graphotherapy import GraphotherapyProgress

router = APIRouter()

@router.get("/correlation", response_model=List[Dict[str, Any]])
def get_crm_wellness_correlation(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    CRM to Wellness Correlation: Identifies high-value leads (Hot/Warm) 
    who have poor focus metrics (Low streaks in Meditation/Grapho).
    """
    # 1. Get High-Value Leads who are also Users (Enrolled)
    high_value_leads = db.query(Lead).filter(
        Lead.status.in_(["hot", "warm"]),
        Lead.email.isnot(None) # Assuming email links Lead to User
    ).all()

    results = []
    for lead in high_value_leads:
        # Find corresponding student user
        user = db.query(User).filter(User.email == lead.email).first()
        if not user:
            continue
            
        # Get Wellness Metrics
        med_progress = db.query(MeditationProgress).filter(MeditationProgress.user_id == user.id).first()
        grapho_progress = db.query(GraphotherapyProgress).filter(GraphotherapyProgress.user_id == user.id).first()
        
        med_streak = med_progress.total_streak if med_progress else 0
        grapho_streak = grapho_progress.total_streak if grapho_progress else 0
        
        # Red Flag Logic: High Value Lead but Streak < 3 days
        is_red_flag = (med_streak < 3 or grapho_streak < 3)
        
        results.append({
            "lead_id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "lead_status": lead.status,
            "lead_source": lead.source,
            "meditation_streak": med_streak,
            "graphotherapy_streak": grapho_streak,
            "is_red_flag": is_red_flag,
            "risk_score": 100 - (min(med_streak, 10) * 5 + min(grapho_streak, 10) * 5) # 0-100 score
        })

    # Sort by risk score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results

@router.get("/summary", response_model=Dict[str, Any])
def get_correlation_summary(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Summary of platform focus health for high-value segments.
    """
    # This would typically be a more complex aggregation query
    all_data = get_crm_wellness_correlation(db, current_admin)
    
    total_high_value = len(all_data)
    red_flags = len([x for x in all_data if x["is_red_flag"]])
    
    avg_risk = sum(x["risk_score"] for x in all_data) / total_high_value if total_high_value > 0 else 0
    
    return {
        "total_enrolled_high_value_leads": total_high_value,
        "active_red_flags": red_flags,
        "average_focus_risk": round(avg_risk, 2),
        "health_status": "CRITICAL" if avg_risk > 60 else "WARNING" if avg_risk > 30 else "HEALTHY"
    }
