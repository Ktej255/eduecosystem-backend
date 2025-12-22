"""
Affiliate Program Models

Models for affiliate marketing program allowing users to earn
commissions by referring new customers.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from app.db.session import Base


class AffiliatePartner(Base):
    """
    Affiliate partners who can earn commissions.
    Users who sign up to promote courses.
    """

    __tablename__ = "affiliate_partners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Referral code
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    custom_slug = Column(String(100), unique=True)  # Optional vanity URL

    # Commission settings
    commission_percentage = Column(
        Numeric(5, 2), default=Decimal("10.00")
    )  # 10% default
    commission_tier = Column(
        String(20), default="standard"
    )  # standard, silver, gold, platinum

    # Earnings
    total_earnings = Column(Numeric(10, 2), default=Decimal("0.00"))
    pending_earnings = Column(Numeric(10, 2), default=Decimal("0.00"))
    paid_earnings = Column(Numeric(10, 2), default=Decimal("0.00"))

    # Statistics
    total_clicks = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2), default=Decimal("0.00"))

    # Status
    status = Column(String(20), default="active")  # active, suspended, inactive
    is_verified = Column(Boolean, default=False)

    # Payout information
    minimum_payout = Column(Numeric(10, 2), default=Decimal("50.00"))
    payout_method = Column(String(20))  # paypal, stripe, bank_transfer
    payout_email = Column(String(255))

    # Tracking
    last_click_date = Column(DateTime(timezone=True))
    last_conversion_date = Column(DateTime(timezone=True))
    last_payout_date = Column(DateTime(timezone=True))

    # Notes
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    referrals = relationship("AffiliateReferral", back_populates="affiliate")
    commissions = relationship("AffiliateCommission", back_populates="affiliate")
    clicks = relationship("AffiliateClick", back_populates="affiliate")


class AffiliateClick(Base):
    """
    Tracks clicks on affiliate links.
    Used for analytics and attribution.
    """

    __tablename__ = "affiliate_clicks"

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(
        Integer, ForeignKey("affiliate_partners.id"), nullable=False, index=True
    )

    # Click details
    referral_code = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer_url = Column(String(500))
    landing_url = Column(String(500))

    # Tracking cookie
    tracking_cookie = Column(String(100), unique=True, index=True)
    cookie_expires_at = Column(DateTime(timezone=True))

    # Conversion tracking
    converted = Column(Boolean, default=False)
    converted_at = Column(DateTime(timezone=True))
    conversion_value = Column(Numeric(10, 2))

    # Geolocation
    country = Column(String(2))
    city = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    affiliate = relationship("AffiliatePartner", back_populates="clicks")


class AffiliateReferral(Base):
    """
    Successful referrals (conversions).
    Tracks referred users and their purchases.
    """

    __tablename__ = "affiliate_referrals"

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(
        Integer, ForeignKey("affiliate_partners.id"), nullable=False, index=True
    )
    referred_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Referral details
    referral_code = Column(String(50), nullable=False)
    tracking_cookie = Column(String(100))

    # Purchase details
    purchase_type = Column(String(20), nullable=False)  # course, bundle, subscription
    purchase_id = Column(Integer, nullable=False)  # ID of course/bundle/subscription
    purchase_amount = Column(Numeric(10, 2), nullable=False)

    # Commission
    commission_percentage = Column(Numeric(5, 2), nullable=False)
    commission_amount = Column(Numeric(10, 2), nullable=False)
    commission_status = Column(String(20), default="pending")  # pending, approved, paid

    # Payment tracking
    payment_id = Column(String(100))

    # Conversion tracking
    first_click_date = Column(DateTime(timezone=True))
    conversion_date = Column(DateTime(timezone=True), server_default=func.now())

    # Refund tracking
    is_refunded = Column(Boolean, default=False)
    refunded_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    affiliate = relationship("AffiliatePartner", back_populates="referrals")
    referred_user = relationship("User", foreign_keys=[referred_user_id])


class AffiliateCommission(Base):
    """
    Commission transactions and payouts.
    Tracks individual commission earnings and payments.
    """

    __tablename__ = "affiliate_commissions"

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(
        Integer, ForeignKey("affiliate_partners.id"), nullable=False, index=True
    )
    referral_id = Column(Integer, ForeignKey("affiliate_referrals.id"), index=True)

    # Commission details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    commission_type = Column(String(20), nullable=False)  # sale, recurring, bonus

    # Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, approved, paid, cancelled

    # Payment tracking
    payout_id = Column(Integer, ForeignKey("affiliate_payouts.id"))
    paid_at = Column(DateTime(timezone=True))

    # Description
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    affiliate = relationship("AffiliatePartner", back_populates="commissions")
    referral = relationship("AffiliateReferral")
    payout = relationship("AffiliatePayout", back_populates="commissions")


class AffiliatePayout(Base):
    """
    Affiliate payout batches.
    Groups multiple commissions into payout requests.
    """

    __tablename__ = "affiliate_payouts"

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(
        Integer, ForeignKey("affiliate_partners.id"), nullable=False, index=True
    )

    # Payout details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Payment method
    payment_method = Column(String(20), nullable=False)
    payment_details = Column(Text)  # Encrypted

    # Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, failed

    # Stripe/PayPal tracking
    stripe_transfer_id = Column(String(100))
    paypal_transaction_id = Column(String(100))
    transaction_id = Column(String(100))

    # Dates
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Notes
    admin_notes = Column(Text)
    failure_reason = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    affiliate = relationship("AffiliatePartner")
    commissions = relationship("AffiliateCommission", back_populates="payout")
