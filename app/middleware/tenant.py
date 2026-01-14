"""
Multi-Tenant Middleware
Detects the organization (tenant) based on the request's Host header.
Sets request.state.organization for downstream use.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.sso import Organization


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get the host from request
        host = request.headers.get("host", "").split(":")[0]  # Remove port if present
        
        # Skip for certain paths (health checks, static, etc.)
        if request.url.path.startswith("/health") or request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Look up organization by domain
        db: Session = SessionLocal()
        try:
            organization = db.query(Organization).filter(
                Organization.domain == host,
                Organization.is_active == True
            ).first()
            
            # Set on request state for downstream access
            request.state.organization = organization
            request.state.organization_id = organization.id if organization else None
            
        finally:
            db.close()
        
        response = await call_next(request)
        return response


def get_current_organization(request: Request) -> Organization | None:
    """Utility to get current organization from request state."""
    return getattr(request.state, "organization", None)
