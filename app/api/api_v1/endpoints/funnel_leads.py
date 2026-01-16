"""
Funnel Leads Management Endpoints
Save and retrieve leads from the graphotherapy funnel
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_db
from app.models.lead import Lead
from app.api import deps
from app.models.user import User

router = APIRouter()


class FunnelLeadCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    source: str = "graphotherapy_funnel"


class FunnelLeadResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    source: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/funnel", response_model=FunnelLeadResponse)
def submit_funnel_lead(
    lead_data: FunnelLeadCreate,
    db: Session = Depends(get_db)
):
    """Submit a lead from the graphotherapy funnel (public endpoint)."""
    # Check if lead exists by email
    existing = db.query(Lead).filter(Lead.email == lead_data.email).first()
    if existing:
        # Update existing lead
        for key, value in lead_data.model_dump().items():
            if value:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new lead
    new_lead = Lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        notes=lead_data.address,  # Using notes field for address
        source=lead_data.source,
        status="new"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


@router.get("/funnel/list", response_model=List[FunnelLeadResponse])
def list_funnel_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_admin_user)
):
    """List all funnel leads (admin only)."""
    leads = db.query(Lead).filter(
        Lead.source == "graphotherapy_funnel"
    ).order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads
