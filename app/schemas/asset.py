from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AssetBase(BaseModel):
    filename: Optional[str] = None
    original_name: Optional[str] = None
    file_type: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None

class AssetCreate(AssetBase):
    filename: str
    original_name: str
    file_type: str
    url: str
    size: int
    user_id: int

class AssetUpdate(AssetBase):
    pass

class AssetInDBBase(AssetBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Asset(AssetInDBBase):
    pass
