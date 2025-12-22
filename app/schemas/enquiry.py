from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Shared properties
class EnquiryBase(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = "new"

# Properties to receive on creation
class EnquiryCreate(EnquiryBase):
    name: str
    email: EmailStr
    subject: str
    message: str

# Properties to receive on update
class EnquiryUpdate(EnquiryBase):
    pass

# Properties shared by models stored in DB
class EnquiryInDBBase(EnquiryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Enquiry(EnquiryInDBBase):
    pass
