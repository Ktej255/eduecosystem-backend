"""
Organization API Endpoints

REST API for managing enterprise organizations with SSO capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.sso import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.services.organization_service import OrganizationService
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
)
async def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    Create a new organization.

    Requires admin privileges.

    - **name**: Organization name
    - **domain**: Primary email domain (e.g., company.com)
    - **slug**: URL-friendly identifier
    - **sso_enabled**: Enable SSO authentication
    - **sso_provider**: SSO provider type
    - **max_users**: Maximum user limit
    """
    service = OrganizationService(db)
    return service.create_organization(organization, current_user.id)


@router.get(
    "/", response_model=List[OrganizationResponse], summary="List Organizations"
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sso_enabled: Optional[bool] = Query(None, description="Filter by SSO enabled"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    List all organizations with optional filters.

    Requires admin privileges.
    """
    service = OrganizationService(db)
    return service.list_organizations(
        skip=skip, limit=limit, is_active=is_active, sso_enabled=sso_enabled
    )


@router.get(
    "/slug/{slug}",
    response_model=OrganizationResponse,
    summary="Get Organization by Slug",
)
async def get_organization_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get organization details by slug.

    Public endpoint - any authenticated user can access.
    """
    service = OrganizationService(db)
    org = service.get_organization_by_slug(slug)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with slug '{slug}' not found",
        )

    return org


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
)
async def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    Get organization details by ID.

    Requires admin privileges.
    """
    service = OrganizationService(db)
    org = service.get_organization(organization_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    return org


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update Organization",
)
async def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    Update organization details.

    Requires admin privileges.
    """
    service = OrganizationService(db)
    return service.update_organization(organization_id, organization)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Organization",
)
async def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"])),
):
    """
    Delete an organization.

    Requires super admin privileges.
    Cannot delete organizations with existing users.
    """
    service = OrganizationService(db)
    service.delete_organization(organization_id)
    return None


@router.get(
    "/{organization_id}/users",
    response_model=List[dict],
    summary="Get Organization Users",
)
async def get_organization_users(
    organization_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    Get all users in an organization.

    Requires admin privileges.
    """
    service = OrganizationService(db)

    # Verify organization exists
    org = service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    users = service.get_organization_users(organization_id, skip, limit)

    # Return sanitized user data
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_sso_user": user.is_sso_user,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.get(
    "/{organization_id}/stats",
    response_model=dict,
    summary="Get Organization Statistics",
)
async def get_organization_stats(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
):
    """
    Get organization statistics.

    Requires admin privileges.
    """
    service = OrganizationService(db)

    # Verify organization exists
    org = service.get_organization(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    user_count = service.get_organization_user_count(organization_id)
    under_limit = service.check_user_limit(organization_id)

    return {
        "organization_id": organization_id,
        "name": org.name,
        "total_users": user_count,
        "max_users": org.max_users,
        "under_limit": under_limit,
        "sso_enabled": org.sso_enabled,
        "sso_enforced": org.sso_enforced,
        "is_active": org.is_active,
    }


@router.get(
    "/detect-from-email/{email}",
    response_model=Optional[OrganizationResponse],
    summary="Detect Organization from Email",
)
async def detect_organization_from_email(email: str, db: Session = Depends(get_db)):
    """
    Detect organization from email domain.

    Public endpoint - useful for SSO login flows.
    Returns null if no organization found.
    """
    service = OrganizationService(db)
    org = service.detect_organization_from_email(email)
    return org


@router.get(
    "/my-organization",
    response_model=Optional[OrganizationResponse],
    summary="Get My Organization",
)
async def get_my_organization(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get the organization for the current user.

    Returns null if user is not part of an organization.
    """
    service = OrganizationService(db)
    org = service.get_user_organization(current_user.id)
    return org
