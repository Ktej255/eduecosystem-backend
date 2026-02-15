from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.crud import upsc_synapse as crud
from app.schemas.upsc_synapse import (
    UPSCCognitiveProfileResponse, UPSCCognitiveProfileCreate, UPSCCognitiveProfileUpdate, 
    UPSCGapAnalysisResponse, UPSCGapAnalysisCreate, 
    UPSCUnlockTransactionResponse, UPSCUnlockTransactionCreate
)

router = APIRouter()

@router.get("/profile", response_model=UPSCCognitiveProfileResponse)
def read_user_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's UPSC Synapse Cognitive Profile.
    """
    profile = crud.get_profile_by_user(db, current_user.id)
    if not profile:
        # Auto-create if not exists
        profile = crud.create_profile(db, UPSCCognitiveProfileCreate(user_id=current_user.id))
    return profile

@router.put("/profile", response_model=UPSCCognitiveProfileResponse)
def update_user_profile(
    *,
    db: Session = Depends(deps.get_db),
    profile_in: UPSCCognitiveProfileUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update cognitive profile (WPS, Stress Index, etc.)
    """
    profile = crud.get_profile_by_user(db, current_user.id)
    if not profile:
        profile = crud.create_profile(db, UPSCCognitiveProfileCreate(user_id=current_user.id))
    
    profile = crud.update_profile(db, profile, profile_in)
    return profile

@router.get("/gap-analysis", response_model=List[UPSCGapAnalysisResponse])
def get_gap_analysis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the Gap Analysis Heatmap data.
    """
    profile = crud.get_profile_by_user(db, current_user.id)
    if not profile:
        return []
    return crud.get_gap_analysis(db, profile.id)

@router.post("/gap-analysis", response_model=UPSCGapAnalysisResponse)
def log_gap_analysis(
    *,
    db: Session = Depends(deps.get_db),
    gap_in: UPSCGapAnalysisCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Log a gap analysis result (Red/Yellow/Green) for a chapter.
    """
    # Verify user owns the profile
    profile = crud.get_profile_by_user(db, current_user.id)
    if not profile or profile.id != gap_in.profile_id:
        raise HTTPException(status_code=400, detail="Profile mismatch")
        
    return crud.create_gap_analysis(db, gap_in)

@router.post("/unlock", response_model=UPSCUnlockTransactionResponse)
def unlock_level(
    *,
    db: Session = Depends(deps.get_db),
    unlock_in: UPSCUnlockTransactionCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Record an unlock transaction (micro-transaction).
    """
    profile = crud.get_profile_by_user(db, current_user.id)
    if not profile or profile.id != unlock_in.profile_id:
        raise HTTPException(status_code=400, detail="Profile mismatch")
        
    return crud.create_unlock_transaction(db, unlock_in)
