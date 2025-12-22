"""
Affiliate API Endpoints

Endpoints for affiliate registration, link generation, and dashboard stats.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.affiliate_service import AffiliateService
from app.schemas.marketplace import (
    AffiliateRegister,
    AffiliateStats,
    AffiliateLinkResponse,
)

router = APIRouter()


@router.post("/register", response_model=AffiliateStats)
def register_affiliate(
    data: AffiliateRegister,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Register as an affiliate partner.
    """
    affiliate = AffiliateService.register_affiliate(
        db=db,
        user_id=current_user.id,
        custom_slug=data.custom_slug,
        payment_method=data.payment_method,
        payout_email=data.payout_email,
    )

    # Return initial stats
    return AffiliateService.get_affiliate_stats(db, current_user.id)


@router.get("/stats", response_model=AffiliateStats)
def get_affiliate_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get affiliate dashboard statistics.
    """
    stats = AffiliateService.get_affiliate_stats(db, current_user.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Affiliate account not found")
    return stats


@router.post("/track/{referral_code}", response_model=AffiliateLinkResponse)
def track_affiliate_click(
    referral_code: str, request: Request, db: Session = Depends(deps.get_db)
):
    """
    Track an affiliate link click (Public endpoint).
    """
    cookie = AffiliateService.track_click(
        db=db,
        referral_code=referral_code,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        referrer_url=request.headers.get("referer"),
        landing_url=str(request.url),
    )

    if not cookie:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    return {"referral_code": referral_code, "tracking_cookie": cookie}
