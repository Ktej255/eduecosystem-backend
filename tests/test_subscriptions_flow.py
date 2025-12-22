"""
Subscription Service Tests

Tests for subscription plan creation, user subscriptions, and billing.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.subscription_service import SubscriptionService
from app.models.user import User


def test_create_subscription_plan(db: Session):
    """Test creating a subscription plan"""
    plan = SubscriptionService.create_plan(
        db=db,
        name="Pro Plan",
        monthly_price=Decimal("29.99"),
        yearly_price=Decimal("299.99"),
        description="Professional features",
        features=["Unlimited courses", "Live classes", "Priority support"],
        access_level="premium",
        trial_days=14,
    )

    assert plan.id is not None
    assert plan.name == "Pro Plan"
    assert plan.slug == "pro-plan"
    assert plan.monthly_price == Decimal("29.99")
    assert plan.yearly_price == Decimal("299.99")
    assert plan.trial_days == 14
    assert plan.access_level == "premium"


def test_create_duplicate_plan(db: Session):
    """Test creating a plan with duplicate name"""
    SubscriptionService.create_plan(
        db=db, name="Basic Plan", monthly_price=Decimal("9.99")
    )

    with pytest.raises(ValueError, match="already exists"):
        SubscriptionService.create_plan(
            db=db, name="Basic Plan", monthly_price=Decimal("9.99")
        )


@pytest.mark.asyncio
async def test_subscribe_user(db: Session, test_user: User):
    """Test subscribing a user to a plan"""
    # Create plan
    plan = SubscriptionService.create_plan(
        db=db, name="Monthly Plan", monthly_price=Decimal("19.99")
    )

    # Subscribe user
    subscription = await SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id, billing_cycle="monthly"
    )

    assert subscription.id is not None
    assert subscription.user_id == test_user.id
    assert subscription.plan_id == plan.id
    assert subscription.billing_cycle == "monthly"
    assert subscription.price_paid == Decimal("19.99")
    assert subscription.status == "active"
    assert subscription.auto_renew is True


@pytest.mark.asyncio
async def test_subscribe_with_trial(db: Session, test_user: User):
    """Test subscription with trial period"""
    plan = SubscriptionService.create_plan(
        db=db, name="Trial Plan", monthly_price=Decimal("29.99"), trial_days=7
    )

    subscription = await SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id, billing_cycle="monthly"
    )

    assert subscription.status == "trial"
    assert subscription.trial_ends_at is not None
    # Trial should end approximately 7 days from now
    days_difference = (subscription.trial_ends_at - datetime.utcnow()).days
    assert 6 <= days_difference <= 8


@pytest.mark.asyncio
async def test_subscribe_yearly(db: Session, test_user: User):
    """Test yearly subscription"""
    plan = SubscriptionService.create_plan(
        db=db,
        name="Yearly Plan",
        monthly_price=Decimal("19.99"),
        yearly_price=Decimal("199.99"),
    )

    subscription = await SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id, billing_cycle="yearly"
    )

    assert subscription.billing_cycle == "yearly"
    assert subscription.price_paid == Decimal("199.99")


@pytest.mark.asyncio
async def test_duplicate_subscription(db: Session, test_user: User):
    """Test preventing duplicate active subscriptions"""
    plan = SubscriptionService.create_plan(
        db=db, name="Duplicate Test", monthly_price=Decimal("9.99")
    )

    # First subscription
    await SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id
    )

    # Try to subscribe again
    with pytest.raises(ValueError, match="already has an active subscription"):
        await SubscriptionService.subscribe_user(
            db=db, user_id=test_user.id, plan_id=plan.id
        )


def test_cancel_subscription_at_period_end(db: Session, test_user: User):
    """Test cancelling subscription at period end"""
    plan = SubscriptionService.create_plan(
        db=db, name="Cancel Test", monthly_price=Decimal("9.99")
    )

    subscription = SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id
    )

    # Cancel at period end
    cancelled = SubscriptionService.cancel_subscription(
        db=db, subscription_id=subscription.id, immediate=False
    )

    assert cancelled.cancel_at_period_end is True
    assert cancelled.auto_renew is False
    assert cancelled.status != "cancelled"  # Not cancelled yet


def test_cancel_subscription_immediately(db: Session, test_user: User):
    """Test immediate subscription cancellation"""
    plan = SubscriptionService.create_plan(
        db=db, name="Immediate Cancel", monthly_price=Decimal("14.99")
    )

    subscription = SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id
    )

    initial_active_count = plan.active_subscriptions

    # Cancel immediately
    cancelled = SubscriptionService.cancel_subscription(
        db=db, subscription_id=subscription.id, immediate=True
    )

    assert cancelled.status == "cancelled"
    assert cancelled.cancelled_at is not None
    assert cancelled.ended_at is not None
    assert plan.active_subscriptions == initial_active_count - 1


def test_check_access(db: Session, test_user: User):
    """Test access control checks"""
    plan = SubscriptionService.create_plan(
        db=db,
        name="Premium Plan",
        monthly_price=Decimal("49.99"),
        access_level="premium",
    )

    # No subscription - no access
    assert SubscriptionService.check_access(db, test_user.id, "standard") is False

    # Subscribe user
    SubscriptionService.subscribe_user(db=db, user_id=test_user.id, plan_id=plan.id)

    # Check access levels
    assert SubscriptionService.check_access(db, test_user.id, "limited") is True
    assert SubscriptionService.check_access(db, test_user.id, "standard") is True
    assert SubscriptionService.check_access(db, test_user.id, "premium") is True
    assert SubscriptionService.check_access(db, test_user.id, "unlimited") is False


def test_get_active_plans(db: Session):
    """Test retrieving active plans"""
    # Create plans
    SubscriptionService.create_plan(
        db=db,
        name="Plan A",
        monthly_price=Decimal("9.99"),
        display_order=1,
        is_active=True,
    )

    SubscriptionService.create_plan(
        db=db,
        name="Plan B",
        monthly_price=Decimal("19.99"),
        display_order=2,
        is_active=True,
    )

    SubscriptionService.create_plan(
        db=db, name="Inactive Plan", monthly_price=Decimal("29.99"), is_active=False
    )

    active_plans = SubscriptionService.get_active_plans(db)

    assert len(active_plans) == 2
    assert active_plans[0].name == "Plan A"
    assert active_plans[1].name == "Plan B"


def test_get_user_subscription(db: Session, test_user: User):
    """Test getting user's current subscription"""
    # No subscription initially
    assert SubscriptionService.get_user_subscription(db, test_user.id) is None

    # Create and subscribe
    plan = SubscriptionService.create_plan(
        db=db, name="User Sub Test", monthly_price=Decimal("12.99")
    )

    subscription = SubscriptionService.subscribe_user(
        db=db, user_id=test_user.id, plan_id=plan.id
    )

    # Get subscription
    user_sub = SubscriptionService.get_user_subscription(db, test_user.id)
    assert user_sub is not None
    assert user_sub.id == subscription.id
