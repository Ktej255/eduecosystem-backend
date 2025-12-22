"""
Affiliate Service

Business logic for affiliate program management, tracking, and commissions.
"""

from sqlalchemy.orm import Session
from app.models.affiliate import (
    AffiliatePartner,
    AffiliateClick,
    AffiliateReferral,
    AffiliateCommission,
)
from app.models.user import User
from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


class AffiliateService:
    """Service for managing affiliate program."""

    @staticmethod
    def register_affiliate(
        db: Session,
        user_id: int,
        custom_slug: Optional[str] = None,
        payment_method: str = "paypal",
        payout_email: Optional[str] = None,
    ) -> AffiliatePartner:
        """
        Register a user as an affiliate.

        Args:
            db: Database session
            user_id: User ID
            custom_slug: Optional vanity URL
            payment_method: Payout method
            payout_email: Payout email address

        Returns:
            AffiliatePartner instance
        """
        # Check if already registered
        existing = (
            db.query(AffiliatePartner)
            .filter(AffiliatePartner.user_id == user_id)
            .first()
        )
        if existing:
            return existing

        # Generate referral code
        user = db.query(User).filter(User.id == user_id).first()
        base_code = custom_slug if custom_slug else user.username
        import re

        base_code = re.sub(r"[^a-z0-9]+", "", base_code.lower())

        # Ensure uniqueness
        referral_code = base_code
        counter = 1
        while (
            db.query(AffiliatePartner)
            .filter(AffiliatePartner.referral_code == referral_code)
            .first()
        ):
            referral_code = f"{base_code}{counter}"
            counter += 1

        affiliate = AffiliatePartner(
            user_id=user_id,
            referral_code=referral_code,
            custom_slug=custom_slug,
            payout_method=payment_method,
            payout_email=payout_email or user.email,
            status="active",
        )

        db.add(affiliate)
        db.commit()
        db.refresh(affiliate)

        logger.info(f"Registered affiliate {user_id} with code {referral_code}")

        return affiliate

    @staticmethod
    def track_click(
        db: Session,
        referral_code: str,
        ip_address: str,
        user_agent: str,
        referrer_url: Optional[str] = None,
        landing_url: Optional[str] = None,
    ) -> str:
        """
        Track an affiliate link click.

        Args:
            db: Database session
            referral_code: Affiliate referral code
            ip_address: Visitor IP
            user_agent: Visitor User Agent
            referrer_url: Source URL
            landing_url: Destination URL

        Returns:
            Tracking cookie value
        """
        affiliate = (
            db.query(AffiliatePartner)
            .filter(
                AffiliatePartner.referral_code == referral_code,
                AffiliatePartner.status == "active",
            )
            .first()
        )

        if not affiliate:
            return None

        # Generate tracking cookie
        tracking_cookie = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)

        click = AffiliateClick(
            affiliate_id=affiliate.id,
            referral_code=referral_code,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer_url=referrer_url,
            landing_url=landing_url,
            tracking_cookie=tracking_cookie,
            cookie_expires_at=expires_at,
        )

        affiliate.total_clicks += 1
        affiliate.last_click_date = datetime.utcnow()

        db.add(click)
        db.commit()

        return tracking_cookie

    @staticmethod
    def process_conversion(
        db: Session,
        user_id: int,
        purchase_type: str,
        purchase_id: int,
        amount: Decimal,
        tracking_cookie: Optional[str] = None,
    ) -> Optional[AffiliateReferral]:
        """
        Process a conversion (sale) from a referral.

        Args:
            db: Database session
            user_id: Purchasing user ID
            purchase_type: 'course', 'bundle', 'subscription'
            purchase_id: ID of item purchased
            amount: Purchase amount
            tracking_cookie: Cookie from user's browser

        Returns:
            AffiliateReferral if successful
        """
        if not tracking_cookie:
            return None

        # Find click
        click = (
            db.query(AffiliateClick)
            .filter(
                AffiliateClick.tracking_cookie == tracking_cookie,
                AffiliateClick.converted == False,
                AffiliateClick.cookie_expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not click:
            return None

        affiliate = click.affiliate

        # Prevent self-referral
        if affiliate.user_id == user_id:
            return None

        # Calculate commission
        commission_amount = amount * (affiliate.commission_percentage / Decimal("100"))

        # Create referral record
        referral = AffiliateReferral(
            affiliate_id=affiliate.id,
            referred_user_id=user_id,
            referral_code=click.referral_code,
            tracking_cookie=tracking_cookie,
            purchase_type=purchase_type,
            purchase_id=purchase_id,
            purchase_amount=amount,
            commission_percentage=affiliate.commission_percentage,
            commission_amount=commission_amount,
            first_click_date=click.created_at,
        )

        db.add(referral)
        db.flush()

        # Create commission record
        commission = AffiliateCommission(
            affiliate_id=affiliate.id,
            referral_id=referral.id,
            amount=commission_amount,
            commission_type="sale",
            status="pending",
            description=f"Commission for {purchase_type} #{purchase_id}",
        )

        db.add(commission)

        # Update click status
        click.converted = True
        click.converted_at = datetime.utcnow()
        click.conversion_value = amount

        # Update affiliate stats
        affiliate.total_conversions += 1
        affiliate.total_earnings += commission_amount
        affiliate.pending_earnings += commission_amount
        affiliate.last_conversion_date = datetime.utcnow()

        # Recalculate conversion rate
        if affiliate.total_clicks > 0:
            affiliate.conversion_rate = (
                Decimal(affiliate.total_conversions) / Decimal(affiliate.total_clicks)
            ) * 100

        db.commit()

        logger.info(
            f"Processed conversion for affiliate {affiliate.referral_code}: ${commission_amount}"
        )

        return referral

    @staticmethod
    def get_affiliate_stats(db: Session, user_id: int) -> Dict:
        """Get dashboard stats for an affiliate."""
        affiliate = (
            db.query(AffiliatePartner)
            .filter(AffiliatePartner.user_id == user_id)
            .first()
        )
        if not affiliate:
            return None

        return {
            "referral_code": affiliate.referral_code,
            "clicks": affiliate.total_clicks,
            "conversions": affiliate.total_conversions,
            "conversion_rate": float(affiliate.conversion_rate),
            "total_earnings": float(affiliate.total_earnings),
            "pending_earnings": float(affiliate.pending_earnings),
            "paid_earnings": float(affiliate.paid_earnings),
        }
