"""
Marketplace Models

Database models for marketplace features including revenue sharing,
instructor payouts, and marketplace listings.
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


class RevenueShare(Base):
    """
    Revenue sharing configuration and tracking for courses.
    Tracks platform and instructor earnings.
    """

    __tablename__ = "revenue_shares"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Revenue split configuration
    platform_fee_percentage = Column(
        Numeric(5, 2), nullable=False, default=Decimal("30.00")
    )
    instructor_percentage = Column(
        Numeric(5, 2), nullable=False, default=Decimal("70.00")
    )

    # Revenue tracking
    total_revenue = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    platform_earnings = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    instructor_earnings = Column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    pending_payout = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # Tracking
    total_enrollments = Column(Integer, default=0)
    last_sale_date = Column(DateTime(timezone=True))
    last_payout_date = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="revenue_share")
    instructor = relationship("User", foreign_keys=[instructor_id])


class InstructorPayout(Base):
    """
    Instructor payout requests and history.
    Tracks payment processing and status.
    """

    __tablename__ = "instructor_payouts"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Payout details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, processing, completed, failed

    # Payment method
    payment_method = Column(String(20), nullable=False)  # stripe, paypal, bank_transfer
    payment_details = Column(Text)  # Encrypted JSON with account details

    # Transaction tracking
    stripe_transfer_id = Column(String(100))
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
    instructor = relationship("User", foreign_keys=[instructor_id])


class InstructorPaymentInfo(Base):
    """
    Instructor payment and tax information.
    Stores encrypted bank details and tax forms.
    """

    __tablename__ = "instructor_payment_info"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Payment methods
    stripe_account_id = Column(String(100))  # Stripe Connect account
    paypal_email = Column(String(255))
    bank_account_encrypted = Column(Text)  # Encrypted bank details

    # Tax information
    tax_country = Column(String(2))  # ISO country code
    tax_id = Column(String(50))  # SSN/EIN/VAT
    tax_form_type = Column(String(20))  # W9, W8BEN, etc.
    tax_form_submitted = Column(Boolean, default=False)
    tax_form_verified = Column(Boolean, default=False)

    # Payout preferences
    minimum_payout_amount = Column(Numeric(10, 2), default=Decimal("50.00"))
    payout_frequency = Column(String(20), default="monthly")  # weekly, monthly, manual

    # Verification
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])


class MarketplaceListing(Base):
    """
    Enhanced marketplace listing for courses.
    Controls visibility, promotion, and marketplace-specific settings.
    """

    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=False, unique=True, index=True
    )

    # Visibility
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_promoted = Column(Boolean, default=False)

    # Marketplace metadata
    marketplace_category = Column(String(100))
    target_audience = Column(String(255))
    learning_outcomes = Column(Text)  # JSON array
    prerequisites = Column(Text)  # JSON array

    # SEO
    seo_title = Column(String(255))
    seo_description = Column(Text)
    seo_keywords = Column(Text)  # Comma-separated

    # Promotion
    featured_until = Column(DateTime(timezone=True))
    promotion_start = Column(DateTime(timezone=True))
    promotion_end = Column(DateTime(timezone=True))

    # Analytics
    view_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2), default=Decimal("0.00"))

    # Ranking
    quality_score = Column(Numeric(3, 2), default=Decimal("0.00"))  # 0-5 rating
    marketplace_rank = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="marketplace_listing")


class RevenueTransaction(Base):
    """
    Individual revenue transactions for detailed tracking.
    Records every sale and its revenue split.
    """

    __tablename__ = "revenue_transactions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Transaction details
    transaction_type = Column(
        String(20), nullable=False
    )  # course, bundle, subscription
    total_amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), nullable=False)
    instructor_earnings = Column(Numeric(10, 2), nullable=False)

    # Payment reference
    payment_id = Column(String(100))
    stripe_payment_intent = Column(String(100))

    # Refund tracking
    is_refunded = Column(Boolean, default=False)
    refunded_at = Column(DateTime(timezone=True))
    refund_amount = Column(Numeric(10, 2))

    # Coupon/discount applied
    coupon_code = Column(String(50))
    discount_amount = Column(Numeric(10, 2), default=Decimal("0.00"))

    # Affiliate commission
    affiliate_id = Column(Integer, ForeignKey("users.id"))
    affiliate_commission = Column(Numeric(10, 2), default=Decimal("0.00"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    course = relationship("Course")
    instructor = relationship("User", foreign_keys=[instructor_id])
    student = relationship("User", foreign_keys=[student_id])
    affiliate = relationship("User", foreign_keys=[affiliate_id])
