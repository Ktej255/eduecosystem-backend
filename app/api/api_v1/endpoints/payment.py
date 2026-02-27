from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api import deps
from app.services.cashfree_service import cashfree_service
import os

router = APIRouter()

from app.models.user import User

class OrderRequest(BaseModel):
    tier: str

@router.post("/create-order")
def create_order(
    request: OrderRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a Cashfree Order for general subscriptions/purchases
    """
    if request.tier != "premium":
        raise HTTPException(status_code=400, detail="Invalid tier requested")
        
    try:
        customer_details = {
            "customer_id": str(current_user.id),
            "customer_email": current_user.email,
            "customer_phone": getattr(current_user, "phone", "9999999999") or "9999999999",
            "customer_name": getattr(current_user, "full_name", current_user.email.split("@")[0]) or "User"
        }

        # Premium cost in INR logic
        premium_amount = 1500.0

        cashfree_order = cashfree_service.create_order(
            order_amount=premium_amount,
            order_currency="INR",
            customer_details=customer_details,
            order_note="Premium Subscription Upgrade",
        )

        # Track this order intentionally for premium upgrades in your db if required
        # For this sprint, we just return the session for checkout
        
        return {
            "order_id": cashfree_order.get("order_id"),
            "payment_session_id": cashfree_order.get("payment_session_id"),
            "amount": premium_amount
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def cashfree_webhook(request: Request, db: Session = Depends(deps.get_db)):
    """
    Cashfree webhook handler for Premium
    """
    try:
        raw_body = await request.body()
        signature = request.headers.get("x-webhook-signature")
        timestamp = request.headers.get("x-webhook-timestamp")

        if not signature or not timestamp:
            raise HTTPException(status_code=400, detail="Missing Cashfree headers")

        # Verify signature
        if not cashfree_service.verify_webhook_signature(signature, timestamp, raw_body.decode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse Event
        event = await request.json()
        
        if event.get("type") == "PAYMENT_SUCCESS_WEBHOOK":
            order = event.get("data", {}).get("order", {})
            order_id = order.get("order_id", "")
            
            # order_id format: ORDER_{customer_id}_{timestamp}
            parts = order_id.split("_")
            if len(parts) >= 2:
                customer_id_str = parts[1]
                if customer_id_str.isdigit():
                    user_id = int(customer_id_str)
                    
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.is_premium = True
                        user.subscription_status = "active"
                        user.is_batch1_authorized = True # Defaulting to unlock access
                        user.is_batch2_authorized = True
                        db.commit()
                        print(f"WEBHOOK SUCCESS: Unlocked Premium for User ID {user_id}")
                    else:
                        print(f"WEBHOOK ERROR: User {user_id} not found.")

        return {"status": "success"}

    except Exception as e:
        print(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

