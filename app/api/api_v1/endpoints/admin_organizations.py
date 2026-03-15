"""
Admin API Endpoints for Organization Management (Multi-Tenancy)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.session import get_db
from app.models.sso import Organization
from app.models.admin_log import AdminLog
from app.api import deps
from app.models.user import User

router = APIRouter()


class OrganizationBase(BaseModel):
    name: str
    domain: str
    slug: str
    logo_url: Optional[str] = None
    theme_config: Optional[dict] = {}
    hero_text: Optional[str] = None
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    logo_url: Optional[str] = None
    theme_config: Optional[dict] = None
    hero_text: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    
    class Config:
        from_attributes = True


@router.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """List all organizations (admin only)."""
    return db.query(Organization).order_by(Organization.id).all()


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    org: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """Create a new organization."""
    existing = db.query(Organization).filter(
        (Organization.domain == org.domain) | (Organization.slug == org.slug)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain or slug already exists")
    
    new_org = Organization(**org.model_dump())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action="create_organization",
        target_type="organization",
        target_id=new_org.id,
        details=f"Created organization '{new_org.name}' with domain '{new_org.domain}'"
    )
    db.add(log)
    db.commit()

    return new_org


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """Get a single organization by ID."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    updates: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """Update an organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    
    db.commit()
    db.refresh(org)

    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action="update_organization",
        target_type="organization",
        target_id=org.id,
        details=f"Updated organization '{org.name}'. Changed fields: {', '.join(updates.model_dump(exclude_unset=True).keys())}"
    )
    db.add(log)
    db.commit()

    return org


@router.delete("/organizations/{org_id}")
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """Delete an organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    db.delete(org)
    db.commit()

    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action="delete_organization",
        target_type="organization",
        target_id=org_id,
        details=f"Deleted organization '{org.name}'"
    )
    db.add(log)
    db.commit()

    return {"success": True, "message": f"Organization '{org.name}' deleted."}
