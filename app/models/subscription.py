"""
Subscription Models

Models for recurring subscription plans allowing unlimited access
to courses and platform features.
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


class SubscriptionPlan(Base):
    """
    Subscription plans (Basic, Pro, Premium).
    Defines pricing, features, and access levels.
    """

    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Plan details
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    short_description = Column(String(500))

    # Pricing
    monthly_price = Column(Numeric(10, 2), nullable=False)
    yearly_price = Column(Numeric(10, 2))  # Optional yearly pricing
    currency = Column(String(3), default="USD")

    # Trial
    trial_days = Column(Integer, default=0)  # 0 = no trial

    # Access level
    access_level = Column(
        String(20), default="limited"
    )  # limited, standard, premium, unlimited
    max_courses = Column(Integer)  # null = unlimited
    max_live_classes = Column(Integer)  # null = unlimited

    # Features (JSON stored as Text)
    features = Column(Text)  # JSON array of features
    included_features = Column(Text)  # JSON array of feature flags

    # Visibility
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_popular = Column(Boolean, default=False)

    # Ordering
    display_order = Column(Integer, default=0)

    # Stripe integration
    stripe_price_id_monthly = Column(String(100))
    stripe_price_id_yearly = Column(String(100))
    stripe_product_id = Column(String(100))

    # Analytics
    total_subscriptions = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    total_revenue = Column(Numeric(10, 2), default=Decimal("0.00"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="plan")


class UserSubscription(Base):
    """
    User subscription instances.
    Tracks individual user subscriptions and billing.
    """

    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(
        Integer, ForeignKey("subscription_plans.id"), nullable=False, index=True
    )

    # Billing cycle
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly

    # Status
    status = Column(
        String(20), nullable=False, default="active"
    )  # trial, active, paused, cancelled, expired

    # Dates
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    trial_ends_at = Column(DateTime(timezone=True))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    # Stripe integration
    stripe_subscription_id = Column(String(100), unique=True, index=True)
    stripe_customer_id = Column(String(100))
    stripe_latest_invoice = Column(String(100))

    # Pricing snapshot (for historical accuracy)
    price_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    cancel_at_period_end = Column(Boolean, default=False)

    # Payment tracking
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    payment_failed_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    invoices = relationship("SubscriptionInvoice", back_populates="subscription")


class SubscriptionInvoice(Base):
    """
    Subscription billing invoices.
    Tracks all subscription payments and invoices.
    """

    __tablename__ = "subscription_invoices"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(
        Integer, ForeignKey("user_subscriptions.id"), nullable=False, index=True
    )

    # Invoice details
    invoice_number = Column(String(50), unique=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Status
    status = Column(
        String(20), nullable=False
    )  # draft, open, paid, void, uncollectible

    # Stripe
    stripe_invoice_id = Column(String(100), unique=True)
    stripe_payment_intent = Column(String(100))

    # Dates
    invoice_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))

    # PDF
    invoice_pdf_url = Column(String(500))

    # Description
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscription = relationship("UserSubscription", back_populates="invoices")


class SubscriptionCoupon(Base):
    """
    Coupons specifically for subscriptions.
    First month/year discounts, etc.
    """

    __tablename__ = "subscription_coupons"

    id = Column(Integer, primary_key=True, index=True)

    # Coupon details
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Discount
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")

    # Application
    applies_to_plans = Column(Text)  # JSON array of plan IDs
    duration = Column(String(20), nullable=False)  # once, repeating, forever
    duration_months = Column(Integer)  # For repeating

    # Validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # Usage limits
    max_redemptions = Column(Integer)  # null = unlimited
    max_redemptions_per_user = Column(Integer, default=1)
    times_redeemed = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
