from typing import Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.upsc_synapse import UPSCCognitiveProfile, UPSCGapAnalysis, UPSCUnlockTransaction
from app.schemas.upsc_synapse import UPSCCognitiveProfileCreate, UPSCCognitiveProfileUpdate, UPSCGapAnalysisCreate, UPSCUnlockTransactionCreate

def get_profile_by_user(db: Session, user_id: int) -> Optional[UPSCCognitiveProfile]:
    return db.query(UPSCCognitiveProfile).filter(UPSCCognitiveProfile.user_id == user_id).first()

def create_profile(db: Session, profile: UPSCCognitiveProfileCreate) -> UPSCCognitiveProfile:
    db_profile = UPSCCognitiveProfile(
        user_id=profile.user_id,
        current_level=profile.current_level,
        wps_score=profile.wps_score,
        stress_index=profile.stress_index
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_profile(db: Session, db_profile: UPSCCognitiveProfile, updates: UPSCCognitiveProfileUpdate) -> UPSCCognitiveProfile:
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def create_gap_analysis(db: Session, gap: UPSCGapAnalysisCreate) -> UPSCGapAnalysis:
    # Check if exists, update if so? Or just append log? 
    # For now, let's assume we update the specific chapter status if exists
    existing = db.query(UPSCGapAnalysis).filter(
        UPSCGapAnalysis.profile_id == gap.profile_id,
        UPSCGapAnalysis.chapter_id == gap.chapter_id
    ).first()

    if existing:
        existing.status = gap.status
        existing.recall_accuracy = gap.recall_accuracy
        existing.last_tested_at = datetime.utcnow()
        if gap.gap_details:
             existing.gap_details = gap.gap_details
        db.commit()
        db.refresh(existing)
        return existing
    
    db_gap = UPSCGapAnalysis(**gap.dict())
    db.add(db_gap)
    db.commit()
    db.refresh(db_gap)
    return db_gap

def get_gap_analysis(db: Session, profile_id: UUID) -> List[UPSCGapAnalysis]:
    return db.query(UPSCGapAnalysis).filter(UPSCGapAnalysis.profile_id == profile_id).all()

def create_unlock_transaction(db: Session, unlock: UPSCUnlockTransactionCreate) -> UPSCUnlockTransaction:
    db_unlock = UPSCUnlockTransaction(**unlock.dict())
    db.add(db_unlock)
    
    # Also update profile
    profile = db.query(UPSCCognitiveProfile).filter(UPSCCognitiveProfile.id == unlock.profile_id).first()
    if profile:
        if unlock.level_unlocked == 'level2':
            profile.is_level2_unlocked = True
        elif unlock.level_unlocked == 'level3':
            profile.is_level3_unlocked = True
            
    db.commit()
    db.refresh(db_unlock)
    return db_unlock
