"""
Stripe Webhook Handlers

Handles webhooks from Stripe for subscription events.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session
import stripe
import os
import logging

from app.api import deps
from app.models.subscription import UserSubscription, SubscriptionInvoice

logger = logging.getLogger(__name__)

router = APIRouter()

# Stripe webhook secret
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: Session = deps.Depends(deps.get_db),
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    Events handled:
    - invoice.payment_succeeded
    - invoice.payment_failed
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    try:
        # Get raw body
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle event
        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Received Stripe event: {event_type}")

        if event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(db, data)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(db, data)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(db, data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(db, data)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_payment_succeeded(db: Session, invoice_data: dict):
    """Handle successful payment"""
    stripe_subscription_id = invoice_data.get("subscription")
    stripe_invoice_id = invoice_data.get("id")
    amount_paid = invoice_data.get("amount_paid", 0) / 100  # Convert from cents

    # Find subscription
    subscription = (
        db.query(UserSubscription)
        .filter(UserSubscription.stripe_subscription_id == stripe_subscription_id)
        .first()
    )

    if not subscription:
        logger.warning(
            f"Subscription not found for Stripe ID: {stripe_subscription_id}"
        )
        return

    # Update subscription
    subscription.last_payment_date = invoice_data.get("created")
    subscription.payment_failed_count = 0
    subscription.status = (
        "active" if subscription.status == "trial" else subscription.status
    )

    # Create/update invoice record
    invoice = (
        db.query(SubscriptionInvoice)
        .filter(SubscriptionInvoice.stripe_invoice_id == stripe_invoice_id)
        .first()
    )

    if not invoice:
        invoice = SubscriptionInvoice(
            subscription_id=subscription.id,
            stripe_invoice_id=stripe_invoice_id,
            amount=amount_paid,
            currency=invoice_data.get("currency", "usd").upper(),
            status="paid",
            invoice_number=invoice_data.get("number"),
            paid_at=invoice_data.get("created"),
        )
        db.add(invoice)
    else:
        invoice.status = "paid"
        invoice.paid_at = invoice_data.get("created")

    # Update plan revenue
    if subscription.plan:
        subscription.plan.total_revenue += amount_paid

    db.commit()
    logger.info(f"Payment succeeded for subscription {subscription.id}")


async def handle_payment_failed(db: Session, invoice_data: dict):
    """Handle failed payment"""
    stripe_subscription_id = invoice_data.get("subscription")

    # Find subscription
    subscription = (
        db.query(UserSubscription)
        .filter(UserSubscription.stripe_subscription_id == stripe_subscription_id)
        .first()
    )

    if not subscription:
        logger.warning(
            f"Subscription not found for Stripe ID: {stripe_subscription_id}"
        )
        return

    # Update subscription
    subscription.payment_failed_count += 1

    # Mark as past_due after 3 failed attempts
    if subscription.payment_failed_count >= 3:
        subscription.status = "past_due"
        logger.warning(f"Subscription {subscription.id} marked as past_due")

    db.commit()
    logger.info(f"Payment failed for subscription {subscription.id}")


async def handle_subscription_updated(db: Session, subscription_data: dict):
    """Handle subscription update from Stripe"""
    stripe_subscription_id = subscription_data.get("id")

    # Find subscription
    subscription = (
        db.query(UserSubscription)
        .filter(UserSubscription.stripe_subscription_id == stripe_subscription_id)
        .first()
    )

    if not subscription:
        logger.warning(
            f"Subscription not found for Stripe ID: {stripe_subscription_id}"
        )
        return

    # Update subscription status
    stripe_status = subscription_data.get("status")
    status_mapping = {
        "active": "active",
        "trialing": "trial",
        "past_due": "past_due",
        "canceled": "cancelled",
        "unpaid": "past_due",
    }
    subscription.status = status_mapping.get(stripe_status, subscription.status)

    # Update period dates
    if subscription_data.get("current_period_start"):
        subscription.current_period_start = subscription_data["current_period_start"]
    if subscription_data.get("current_period_end"):
        subscription.current_period_end = subscription_data["current_period_end"]
        subscription.next_payment_date = subscription_data["current_period_end"]

    # Check cancel_at_period_end
    subscription.cancel_at_period_end = subscription_data.get(
        "cancel_at_period_end", False
    )

    db.commit()
    logger.info(f"Subscription {subscription.id} updated from Stripe")


async def handle_subscription_deleted(db: Session, subscription_data: dict):
    """Handle subscription deletion from Stripe"""
    stripe_subscription_id = subscription_data.get("id")

    # Find subscription
    subscription = (
        db.query(UserSubscription)
        .filter(UserSubscription.stripe_subscription_id == stripe_subscription_id)
        .first()
    )

    if not subscription:
        logger.warning(
            f"Subscription not found for Stripe ID: {stripe_subscription_id}"
        )
        return

    # Mark as cancelled
    subscription.status = "cancelled"
    subscription.ended_at = subscription_data.get("ended_at")

    # Update plan active count
    if subscription.plan and subscription.plan.active_subscriptions > 0:
        subscription.plan.active_subscriptions -= 1

    db.commit()
    logger.info(f"Subscription {subscription.id} cancelled from Stripe")
