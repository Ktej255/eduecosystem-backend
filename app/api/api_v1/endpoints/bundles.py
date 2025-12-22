"""
Bundle API Endpoints

Endpoints for creating, managing, and enrolling in course bundles.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.api import deps
from app.models.user import User
from app.services.bundle_service import BundleService
from app.schemas.marketplace import BundleCreate, BundleResponse

router = APIRouter()


@router.post("/", response_model=BundleResponse)
def create_bundle(
    bundle_in: BundleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create a new course bundle (Instructor only).
    """
    # Verify user is instructor
    # In a real app, check role. Assuming active user can create for now.
    try:
        return BundleService.create_bundle(
            db=db,
            instructor_id=current_user.id,
            title=bundle_in.title,
            description=bundle_in.description,
            course_ids=bundle_in.course_ids,
            discount_percentage=bundle_in.discount_percentage,
            slug=bundle_in.slug,
            thumbnail_url=bundle_in.thumbnail_url,
            is_published=bundle_in.is_published,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{bundle_id}", response_model=BundleResponse)
def get_bundle(bundle_id: int, db: Session = Depends(deps.get_db)):
    """
    Get bundle details.
    """
    bundle = BundleService.get_bundle_details(db, bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return bundle


@router.post("/{bundle_id}/enroll")
async def enroll_in_bundle(
    bundle_id: int,
    payment_id: str,
    amount: Decimal,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Enroll in a bundle.
    """
    try:
        enrollment = await BundleService.enroll_in_bundle(
            db=db,
            user_id=current_user.id,
            bundle_id=bundle_id,
            payment_id=payment_id,
            price_paid=amount,
        )
        return {
            "message": "Successfully enrolled in bundle",
            "enrollment_id": enrollment.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/featured", response_model=List[BundleResponse])
def get_featured_bundles(limit: int = 10, db: Session = Depends(deps.get_db)):
    """
    Get featured bundles for homepage.
    """
    return BundleService.get_featured_bundles(db, limit)
