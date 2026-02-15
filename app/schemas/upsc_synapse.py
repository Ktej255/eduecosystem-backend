from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4
from datetime import datetime

# --- COGNITIVE PROFILE ---
class UPSCCognitiveProfileBase(BaseModel):
    current_level: str = "level1"
    wps_score: float = 0.0
    stress_index: float = 0.0
    is_level2_unlocked: bool = False
    is_level3_unlocked: bool = False

class UPSCCognitiveProfileCreate(UPSCCognitiveProfileBase):
    user_id: int

class UPSCCognitiveProfileUpdate(BaseModel):
    current_level: Optional[str] = None
    wps_score: Optional[float] = None
    stress_index: Optional[float] = None
    is_level2_unlocked: Optional[bool] = None
    is_level3_unlocked: Optional[bool] = None

class UPSCCognitiveProfileResponse(UPSCCognitiveProfileBase):
    id: UUID4
    user_id: int
    last_updated: datetime

    class Config:
        from_attributes = True

# --- GAP ANALYSIS ---
class UPSCGapAnalysisBase(BaseModel):
    chapter_id: int
    subject: str = "Polity"
    status: str = "unattempted"
    recall_accuracy: float = 0.0
    gap_details: Optional[Dict[str, Any]] = None

class UPSCGapAnalysisCreate(UPSCGapAnalysisBase):
    profile_id: UUID4

class UPSCGapAnalysisResponse(UPSCGapAnalysisBase):
    id: UUID4
    last_tested_at: datetime
    
    class Config:
        from_attributes = True

# --- UNLOCK TRANSACTION ---
class UPSCUnlockTransactionBase(BaseModel):
    level_unlocked: str
    amount_paid: float
    currency: str = "INR"
    transaction_id: Optional[str] = None
    status: str = "completed"

class UPSCUnlockTransactionCreate(UPSCUnlockTransactionBase):
    profile_id: UUID4

class UPSCUnlockTransactionResponse(UPSCUnlockTransactionBase):
    id: UUID4
    unlocked_at: datetime
    
    class Config:
        from_attributes = True
