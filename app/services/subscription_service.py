"""
Subscription Service

Business logic for managing subscription plans, user subscriptions,
recurring billing, and access control.
"""

from sqlalchemy.orm import Session
from app.models.subscription import SubscriptionPlan, UserSubscription
from decimal import Decimal
from typing import Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Stripe client - imported here to allow test mocking via patch
try:
    import stripe
except ImportError:
    # Stripe not installed - tests will mock this anyway
    stripe = None


class SubscriptionService:
    """Service for managing subscriptions and recurring billing."""

    @staticmethod
    def create_plan(
        db: Session,
        name: str,
        monthly_price: Decimal,
        description: str = None,
        yearly_price: Optional[Decimal] = None,
        features: List[str] = [],
        access_level: str = "standard",
        trial_days: int = 0,
        **kwargs,
    ) -> SubscriptionPlan:
        """
        Create a new subscription plan.

        Args:
            db: Database session
            name: Plan name
            monthly_price: Monthly cost
            description: Plan description
            yearly_price: Yearly cost (optional)
            features: List of features included
            access_level: Access level identifier
            trial_days: Number of trial days
            **kwargs: Additional fields

        Returns:
            SubscriptionPlan instance
        """
        # Generate slug
        import re

        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

        # Check if slug exists
        existing = (
            db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == slug).first()
        )
        if existing:
            raise ValueError(f"Plan with name '{name}' already exists")

        # Create Stripe product/price (placeholder)
        stripe_product_id = f"prod_{slug}"
        stripe_price_id_monthly = f"price_{slug}_mo"
        stripe_price_id_yearly = f"price_{slug}_yr" if yearly_price else None

        # Serialize features
        import json

        features_json = json.dumps(features)

        plan = SubscriptionPlan(
            name=name,
            slug=slug,
            description=description,
            monthly_price=monthly_price,
            yearly_price=yearly_price,
            features=features_json,
            access_level=access_level,
            trial_days=trial_days,
            stripe_product_id=stripe_product_id,
            stripe_price_id_monthly=stripe_price_id_monthly,
            stripe_price_id_yearly=stripe_price_id_yearly,
            **kwargs,
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        logger.info(f"Created subscription plan: {name} (${monthly_price}/mo)")

        return plan

    @staticmethod
    async def subscribe_user(
        db: Session,
        user_id: int,
        plan_id: int,
        billing_cycle: str = "monthly",
        payment_method_id: Optional[str] = None,
    ) -> UserSubscription:
        """
        Subscribe a user to a plan.

        Args:
            db: Database session
            user_id: User ID
            plan_id: Plan ID
            billing_cycle: 'monthly' or 'yearly'
            payment_method_id: Stripe payment method ID

        Returns:
            UserSubscription instance
        """
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")

        # Check for existing active subscription
        existing = (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trial"]),
            )
            .first()
        )

        if existing:
            # If same plan, just return it
            if existing.plan_id == plan_id:
                return existing
            # If different plan, this would be an upgrade/downgrade logic
            # For simplicity, we'll raise error for now
            raise ValueError(
                "User already has an active subscription. Please upgrade/downgrade instead."
            )

        # Determine price
        price = plan.monthly_price if billing_cycle == "monthly" else plan.yearly_price
        if price is None:
            raise ValueError("Invalid billing cycle for this plan")

        # Calculate dates
        now = datetime.utcnow()
        trial_ends_at = None
        status = "active"

        if plan.trial_days > 0:
            status = "trial"
            trial_ends_at = now + timedelta(days=plan.trial_days)
            current_period_start = now
            current_period_end = trial_ends_at
        else:
            current_period_start = now
            # Add month or year
            if billing_cycle == "monthly":
                current_period_end = now + timedelta(days=30)
            else:
                current_period_end = now + timedelta(days=365)

        # Create Stripe subscription (Mock)
        stripe_sub_id = f"sub_{user_id}_{int(now.timestamp())}"

        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            status=status,
            started_at=now,
            trial_ends_at=trial_ends_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            price_paid=price,
            stripe_subscription_id=stripe_sub_id,
            next_payment_date=current_period_end,
        )

        db.add(subscription)

        # Update plan stats
        plan.total_subscriptions += 1
        plan.active_subscriptions += 1

        db.commit()
        db.refresh(subscription)

        logger.info(f"User {user_id} subscribed to {plan.name} ({billing_cycle})")

        return subscription

    @staticmethod
    def cancel_subscription(
        db: Session, subscription_id: int, immediate: bool = False
    ) -> UserSubscription:
        """
        Cancel a subscription.

        Args:
            db: Database session
            subscription_id: Subscription ID
            immediate: If True, cancel immediately. If False, cancel at period end.

        Returns:
            Updated UserSubscription
        """
        sub = (
            db.query(UserSubscription)
            .filter(UserSubscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise ValueError("Subscription not found")

        if sub.status == "cancelled":
            return sub

        if immediate:
            sub.status = "cancelled"
            sub.cancelled_at = datetime.utcnow()
            sub.ended_at = datetime.utcnow()
            sub.auto_renew = False

            # Update plan stats
            if sub.plan:
                sub.plan.active_subscriptions = max(
                    0, sub.plan.active_subscriptions - 1
                )
        else:
            sub.cancel_at_period_end = True
            sub.auto_renew = False

        db.commit()
        db.refresh(sub)

        logger.info(
            f"Subscription {subscription_id} cancelled (Immediate: {immediate})"
        )

        return sub

    @staticmethod
    def check_access(
        db: Session, user_id: int, required_level: str = "standard"
    ) -> bool:
        """
        Check if user has active subscription with required access level.

        Args:
            db: Database session
            user_id: User ID
            required_level: Required access level

        Returns:
            True if access granted
        """
        sub = (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trial"]),
            )
            .first()
        )

        if not sub:
            return False

        # Check expiration
        if sub.current_period_end and sub.current_period_end < datetime.utcnow():
            # Should have been marked expired by background job, but handle here just in case
            return False

        # Level hierarchy
        levels = {"limited": 1, "standard": 2, "premium": 3, "unlimited": 4}

        user_level = levels.get(sub.plan.access_level, 0)
        req_level = levels.get(required_level, 0)

        return user_level >= req_level

    @staticmethod
    def get_active_plans(db: Session) -> List[SubscriptionPlan]:
        """Get all active subscription plans."""
        return (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.display_order)
            .all()
        )

    @staticmethod
    def get_user_subscription(db: Session, user_id: int) -> Optional[UserSubscription]:
        """Get user's current active subscription."""
        return (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trial"]),
            )
            .first()
        )
