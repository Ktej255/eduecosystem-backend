from typing import Dict, Any, Optional
from pydantic import BaseModel

class AppConfigBase(BaseModel):
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None

class AppConfigCreate(AppConfigBase):
    pass

class AppConfigUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class AppConfigInDBBase(AppConfigBase):
    id: int

    class Config:
        from_attributes = True

class AppConfig(AppConfigInDBBase):
    pass
