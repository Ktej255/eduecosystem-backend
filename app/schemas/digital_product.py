from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime

# Shared properties
class DigitalProductBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    is_active: Optional[bool] = True

# Properties to receive on creation
class DigitalProductCreate(DigitalProductBase):
    title: str
    price: Decimal
    file_url: str

# Properties to receive on update
class DigitalProductUpdate(DigitalProductBase):
    pass

# Properties shared by models stored in DB
class DigitalProductInDBBase(DigitalProductBase):
    id: int
    instructor_id: int
    sales_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class DigitalProduct(DigitalProductInDBBase):
    pass
