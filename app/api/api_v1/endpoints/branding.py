"""
Public Tenant Branding Endpoint
Returns organization theme/branding based on the current domain.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any


router = APIRouter()


class BrandingResponse(BaseModel):
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    logo_url: Optional[str] = None
    theme_config: Dict[str, Any] = {}
    hero_text: Optional[str] = None
    is_custom_domain: bool = False


@router.get("/branding", response_model=BrandingResponse)
def get_branding(request: Request):
    """
    Returns brand configuration for the current domain.
    Used by frontend to dynamically theme based on which domain is accessed.
    """
    org = getattr(request.state, "organization", None)
    
    if org:
        return BrandingResponse(
            organization_id=org.id,
            organization_name=org.name,
            logo_url=org.logo_url,
            theme_config=org.theme_config or {},
            hero_text=org.hero_text,
            is_custom_domain=True
        )
    
    # Default branding (main platform)
    return BrandingResponse(
        organization_name="Eduecosystem",
        logo_url="/logo.png",
        theme_config={"primary_color": "#6366f1"},
        hero_text="Transform Your Mind Through Graphotherapy",
        is_custom_domain=False
    )
