from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.core import payment
from app.core.config import settings
import stripe

router = APIRouter()


@router.post("/checkout-session")
def create_checkout_session(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a Stripe Checkout Session for premium subscription.
    """
    try:
        checkout_session = payment.create_checkout_session(
            user_id=current_user.id, user_email=current_user.email
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(deps.get_db)):
    """
    Stripe webhook handler.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment.handle_checkout_session(session, db)

    elif event["type"] == "customer.subscription.updated":
        # Handle subscription updates (renewals, cancellations)
        pass

    elif event["type"] == "customer.subscription.deleted":
        # Handle subscription expiration
        pass

    return {"status": "success"}


@router.post("/portal")
def create_portal_session(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a Stripe Customer Portal session.
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        session = payment.create_portal_session(current_user.stripe_customer_id)
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subscription")
def cancel_subscription(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel premium subscription.
    """
    # In a real app, you'd store subscription_id on the user model too
    # For now, we'd need to fetch it from Stripe or assume logic
    raise HTTPException(
        status_code=501, detail="Not implemented yet - requires subscription_id storage"
    )
