from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.course import Course


# Shared properties
class BundleBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    currency: str = "INR"
    thumbnail_url: Optional[str] = None
    is_published: bool = False


# Properties to receive on creation
class BundleCreate(BundleBase):
    course_ids: List[int]


# Properties to receive on update
class BundleUpdate(BundleBase):
    title: Optional[str] = None
    price: Optional[float] = None
    course_ids: Optional[List[int]] = None


# Properties shared by models stored in DB
class BundleInDBBase(BundleBase):
    id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Bundle(BundleInDBBase):
    courses: List[Course] = []
    total_value: Optional[float] = None  # Calculated field for display


# Properties stored in DB
class BundleInDB(BundleInDBBase):
    pass
