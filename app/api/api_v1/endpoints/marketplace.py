"""
Marketplace API Endpoints

Endpoints for marketplace administration, revenue tracking, and payout management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.api import deps
from app.models.user import User
from app.services.revenue_service import RevenueShareService
from app.services.payout_service import PayoutService
from app.schemas.marketplace import RevenueStats, PayoutResponse, InstructorEarnings

router = APIRouter()

# --- Instructor Endpoints ---


@router.get("/earnings", response_model=InstructorEarnings)
def get_my_earnings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get current user's instructor earnings summary.
    """
    # Verify user is an instructor (has created courses)
    # This check could be more robust based on user roles
    return RevenueShareService.get_instructor_earnings(db, current_user.id)


@router.post("/payouts/request", response_model=PayoutResponse)
def request_payout(
    amount: Optional[Decimal] = None,
    payment_method: str = "stripe",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Request a payout of available earnings.
    """
    try:
        payout = PayoutService.request_instructor_payout(
            db, current_user.id, amount, payment_method
        )
        return payout
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payouts/history", response_model=List[PayoutResponse])
def get_payout_history(
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get payout history for the current instructor.
    """
    return PayoutService.get_instructor_payout_history(db, current_user.id, limit)


# --- Admin Endpoints ---


@router.get("/admin/revenue", response_model=RevenueStats)
def get_platform_revenue(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Get platform-wide revenue statistics (Admin only).
    """
    return RevenueShareService.get_platform_revenue_summary(db, start_date, end_date)


@router.get("/admin/payouts/pending", response_model=List[PayoutResponse])
def get_pending_payouts(
    payout_type: str = "instructor",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Get all pending payout requests (Admin only).
    """
    return PayoutService.get_pending_payouts(db, payout_type)


@router.post("/admin/payouts/{payout_id}/process")
async def process_payout(
    payout_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Process a pending payout (Admin only).
    """
    success = await PayoutService.process_instructor_payout(
        db, payout_id, current_user.id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process payout")
    return {"message": "Payout processed successfully"}


@router.post("/admin/payouts/auto-process")
def trigger_auto_payouts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Trigger automatic monthly payouts processing (Admin only).
    """
    payout_ids = PayoutService.process_automatic_payouts(db)
    return {
        "message": f"Created {len(payout_ids)} automatic payouts",
        "payout_ids": payout_ids,
    }
