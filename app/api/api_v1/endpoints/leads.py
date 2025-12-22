from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import crud, models, schemas
from app.api import deps
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate, Lead as LeadSchema, BulkReassignRequest
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[LeadSchema])
def read_leads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    source: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve leads with filtering.
    """
    query = db.query(Lead)
    
    # If not admin/superuser, maybe restrict to assigned leads?
    # For now, let's assume admins/teachers can see detailed leads, or maybe just check permissions.
    # Allowing all active users to read for now, but in real app would verify specific permissions.
    
    if status:
        query = query.filter(Lead.status == status)
    
    if source:
        query = query.filter(or_(
            Lead.source_primary == source,
            Lead.source_secondary == source,
            Lead.source_tertiary == source
        ))
        
    if assigned_to_id:
        query = query.filter(Lead.assigned_to_id == assigned_to_id)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(or_(
            Lead.name.ilike(search_filter),
            Lead.email.ilike(search_filter),
            Lead.phone.ilike(search_filter)
        ))
    
    leads = query.offset(skip).limit(limit).all()
    return leads

@router.post("/", response_model=LeadSchema)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new lead.
    """
    # Check for duplication (simple check by email)
    existing_lead = db.query(Lead).filter(Lead.email == lead_in.email).first()
    if existing_lead:
        # Update logic could go here for "Zero Lead Leakage" - e.g. add new source as secondary/tertiary if empty
        # For now, just return existing or error? 
        # Requirement says "Eliminate lead duplication" and "source attribution... ensures... track multiple source levels"
        # So we should probably update the existing lead's secondary/tertiary sources if they are empty
        
        updated = False
        if not existing_lead.source_secondary and lead_in.source_primary != existing_lead.source_primary:
             existing_lead.source_secondary = lead_in.source_primary
             updated = True
        elif not existing_lead.source_tertiary and lead_in.source_primary != existing_lead.source_primary and lead_in.source_primary != existing_lead.source_secondary:
             existing_lead.source_tertiary = lead_in.source_primary
             updated = True
             
        if updated:
            db.commit()
            db.refresh(existing_lead)
        
        return existing_lead

    lead = Lead(**lead_in.dict())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.put("/{id}", response_model=LeadSchema)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    lead_in: LeadUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a lead.
    """
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    update_data = lead_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
        
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.post("/bulk-reassign", response_model=List[LeadSchema])
def bulk_reassign_leads(
    *,
    db: Session = Depends(deps.get_db),
    reassign_data: BulkReassignRequest,
    current_user: models.User = Depends(deps.get_current_active_superuser), # restricted to superuser or admin
) -> Any:
    """
    Bulk reassign leads to a different user.
    """
    leads = db.query(Lead).filter(Lead.id.in_(reassign_data.lead_ids)).all()
    
    target_user = db.query(User).filter(User.id == reassign_data.assigned_to_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
        
    for lead in leads:
        lead.assigned_to_id = target_user.id
        
    db.commit()
    # Return updated leads
    return leads # This might be inefficient for large lists, maybe return count? sticking to schema for now.

@router.post("/{id}/verify", response_model=LeadSchema)
def verify_lead(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    method: str = Query(..., regex="^(EMAIL|SMS|WHATSAPP)$"),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually mark a lead as verified (simulating the verification process).
    """
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.is_verified = True
    lead.verification_method = method
    # Simple logic: increase intent score
    lead.intent_score = min((lead.intent_score or 0) + 0.5, 1.0) 
    
    db.commit()
    db.refresh(lead)
    return lead
