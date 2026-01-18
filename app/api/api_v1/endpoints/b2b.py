from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Dict
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.b2b import Organization, OrganizationMember

router = APIRouter()

@router.post("/orgs", response_model=Dict[str, Any])
def create_organization(
    name: str,
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new organization.
    """
    org = Organization(name=name, domain=domain)
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Add creator as Admin
    member = OrganizationMember(organization_id=org.id, user_id=current_user.id, role="admin")
    db.add(member)
    db.commit()
    
    return {"id": org.id, "name": org.name, "message": "Organization created successfully"}

@router.get("/orgs/dashboard", response_model=Dict[str, Any])
def get_org_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get analytics for the user's organization.
    """
    # 1. Find user's org
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    if not member:
         # Return demo data if not part of an org
         return {
             "org_name": "Demo Corp",
             "total_employees": 150,
             "active_learners": 120,
             "avg_skill_score": 78,
             "top_skills": ["Polity", "Ethics", "Communication"],
             "skills_matrix": [
                 {"name": "Alice", "polity": 85, "ethics": 90, "total": 175},
                 {"name": "Bob", "polity": 40, "ethics": 60, "total": 100},
                 {"name": "Charlie", "polity": 70, "ethics": 75, "total": 145}
             ]
         }
    
    # Real implementation would query DB
    return {
         "org_name": member.organization.name,
         "total_employees": 12,
         "active_learners": 8,
         "avg_skill_score": 65,
         "top_skills": ["General"],
         "skills_matrix": []
    }
