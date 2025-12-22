"""
AI Avatar Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class AIAvatarBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    purpose: str = Field(..., pattern="^(sales|support|engage|generic)$")
    personality: Optional[str] = None
    tone: str = Field(default="professional", pattern="^(professional|casual|friendly|formal)$")
    response_style: str = Field(default="concise", pattern="^(concise|detailed|conversational)$")
    knowledge_base: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True


class AIAvatarCreate(AIAvatarBase):
    user_id: int


class AIAvatarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    personality: Optional[str] = None
    tone: Optional[str] = Field(None, pattern="^(professional|casual|friendly|formal)$")
    response_style: Optional[str] = Field(None, pattern="^(concise|detailed|conversational)$")
    knowledge_base: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AIAvatarResponse(AIAvatarBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
