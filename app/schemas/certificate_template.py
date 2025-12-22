from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# Base schemas
class CertificateTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    background_url: Optional[str] = None
    background_color: str = "#ffffff"
    layout: Optional[dict] = {}
    title_font: str = "Arial"
    title_font_size: int = 48
    title_color: str = "#000000"
    body_font: str = "Arial"
    body_font_size: int = 24
    body_color: str = "#333333"
    border_style: str = "none"
    border_color: str = "#000000"
    logo_url: Optional[str] = None
    signature_url: Optional[str] = None
    is_public: bool = True


class CertificateTemplateCreate(CertificateTemplateBase):
    pass


class CertificateTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    background_url: Optional[str] = None
    background_color: Optional[str] = None
    layout: Optional[dict] = None
    title_font: Optional[str] = None
    title_font_size: Optional[int] = None
    title_color: Optional[str] = None
    body_font: Optional[str] = None
    body_font_size: Optional[int] = None
    body_color: Optional[str] = None
    border_style: Optional[str] = None
    border_color: Optional[str] = None
    logo_url: Optional[str] = None
    signature_url: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None


class CertificateTemplate(CertificateTemplateBase):
    id: int
    is_default: bool
    creator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateTemplateList(BaseModel):
    """Paginated list of certificate templates"""

    items: list[CertificateTemplate]
    total: int
    page: int
    page_size: int
