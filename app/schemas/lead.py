from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Shared properties
class LeadBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    status: Optional[str] = "NEW"
    source_primary: Optional[str] = None
    source_secondary: Optional[str] = None
    source_tertiary: Optional[str] = None
    assigned_to_id: Optional[int] = None
    is_verified: Optional[bool] = False
    verification_method: Optional[str] = None
    intent_score: Optional[float] = 0.0
    notes: Optional[str] = None

# Properties to receive on lead creation
class LeadCreate(LeadBase):
    pass

# Properties to receive on lead update
class LeadUpdate(LeadBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Properties shared by models stored in DB
class LeadInDBBase(LeadBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Properties to return to client
class Lead(LeadInDBBase):
    pass

# Additional schemas
class LeadFilter(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    assigned_to: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class BulkReassignRequest(BaseModel):
    lead_ids: List[int]
    assigned_to_id: int
