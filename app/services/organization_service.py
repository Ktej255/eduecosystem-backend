"""
Organization Service

Business logic for managing organizations with SSO capabilities.
Handles organization CRUD, domain verification, and user management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.sso import Organization
from app.models.user import User
from app.schemas.sso import OrganizationCreate, OrganizationUpdate
import re


class OrganizationService:
    """Service for organization management"""

    def __init__(self, db: Session):
        self.db = db

    def create_organization(
        self, org_data: OrganizationCreate, created_by_user_id: Optional[int] = None
    ) -> Organization:
        """
        Create a new organization.

        Args:
            org_data: Organization creation data
            created_by_user_id: ID of user creating the organization

        Returns:
            Created organization

        Raises:
            HTTPException: If domain or slug already exists
        """
        # Validate domain format
        if not self._is_valid_domain(org_data.domain):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid domain format"
            )

        # Check if domain already exists
        existing = (
            self.db.query(Organization)
            .filter(Organization.domain == org_data.domain)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with domain '{org_data.domain}' already exists",
            )

        # Check if slug already exists
        existing_slug = (
            self.db.query(Organization)
            .filter(Organization.slug == org_data.slug)
            .first()
        )
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization slug '{org_data.slug}' already taken",
            )

        # Create organization
        org = Organization(**org_data.model_dump())
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)

        return org

    def get_organization(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return self.db.query(Organization).filter(Organization.slug == slug).first()

    def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain"""
        return self.db.query(Organization).filter(Organization.domain == domain).first()

    def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        sso_enabled: Optional[bool] = None,
    ) -> List[Organization]:
        """
        List organizations with optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status
            sso_enabled: Filter by SSO enabled status

        Returns:
            List of organizations
        """
        query = self.db.query(Organization)

        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)

        if sso_enabled is not None:
            query = query.filter(Organization.sso_enabled == sso_enabled)

        return query.offset(skip).limit(limit).all()

    def update_organization(
        self, org_id: int, org_data: OrganizationUpdate
    ) -> Organization:
        """
        Update an organization.

        Args:
            org_id: Organization ID
            org_data: Update data

        Returns:
            Updated organization

        Raises:
            HTTPException: If organization not found or domain/slug conflict
        """
        org = self.get_organization(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {org_id} not found",
            )

        update_data = org_data.model_dump(exclude_unset=True)

        # Check domain uniqueness if being updated
        if "domain" in update_data and update_data["domain"] != org.domain:
            if not self._is_valid_domain(update_data["domain"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid domain format",
                )

            existing = (
                self.db.query(Organization)
                .filter(
                    and_(
                        Organization.domain == update_data["domain"],
                        Organization.id != org_id,
                    )
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Domain '{update_data['domain']}' already in use",
                )

        # Check slug uniqueness if being updated
        if "slug" in update_data and update_data["slug"] != org.slug:
            existing = (
                self.db.query(Organization)
                .filter(
                    and_(
                        Organization.slug == update_data["slug"],
                        Organization.id != org_id,
                    )
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Slug '{update_data['slug']}' already in use",
                )

        # Update organization
        for field, value in update_data.items():
            setattr(org, field, value)

        self.db.commit()
        self.db.refresh(org)

        return org

    def delete_organization(self, org_id: int) -> bool:
        """
        Delete an organization.

        Args:
            org_id: Organization ID

        Returns:
            True if deleted

        Raises:
            HTTPException: If organization not found or has users
        """
        org = self.get_organization(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {org_id} not found",
            )

        # Check if organization has users
        user_count = self.db.query(User).filter(User.organization_id == org_id).count()

        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete organization with {user_count} users. Remove users first.",
            )

        self.db.delete(org)
        self.db.commit()

        return True

    def get_organization_users(
        self, org_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get all users in an organization"""
        return (
            self.db.query(User)
            .filter(User.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_organization_user_count(self, org_id: int) -> int:
        """Get total user count for organization"""
        return self.db.query(User).filter(User.organization_id == org_id).count()

    def check_user_limit(self, org_id: int) -> bool:
        """
        Check if organization has reached user limit.

        Returns:
            True if under limit or no limit set, False if limit reached
        """
        org = self.get_organization(org_id)
        if not org or not org.max_users:
            return True  # No limit

        current_count = self.get_organization_user_count(org_id)
        return current_count < org.max_users

    def verify_domain_ownership(
        self, org_id: int, verification_method: str = "dns"
    ) -> bool:
        """
        Verify domain ownership (placeholder for actual verification).

        In production, this would:
        - DNS: Check for TXT record with verification code
        - Email: Send verification email to admin@domain
        - File: Check for verification file at domain/.well-known/

        Args:
            org_id: Organization ID
            verification_method: Method to verify (dns, email, file)

        Returns:
            True if verified
        """
        # TODO: Implement actual domain verification
        # For now, just return True for development
        return True

    def get_user_organization(self, user_id: int) -> Optional[Organization]:
        """Get organization for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.organization_id:
            return self.get_organization(user.organization_id)
        return None

    def detect_organization_from_email(self, email: str) -> Optional[Organization]:
        """
        Detect organization from email domain.

        Args:
            email: User email address

        Returns:
            Organization if found, None otherwise
        """
        if "@" not in email:
            return None

        domain = email.split("@")[1].lower()
        return self.get_organization_by_domain(domain)

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        """Validate domain format"""
        pattern = r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$"
        return bool(re.match(pattern, domain.lower()))

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from organization name"""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug[:100]  # Max length
