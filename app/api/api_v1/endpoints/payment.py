from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api import deps
from app.services.cashfree_service import cashfree_service
from app.models.user import User
from app.models.meditation import MeditationProgress, MEDITATION_LEVELS
from app.models.graphotherapy import GraphotherapyProgress, GRAPHOTHERAPY_LEVELS
import os
import json

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://eduecosystem-frontend.vercel.app")

router = APIRouter()

# Product catalog — single source of truth for subject pricing
SUBJECT_PRODUCTS = {
    "geography": {"name": "Geography for UPSC 2026", "price": 499.0},
    "polity": {"name": "Polity (Laxmikanth 95 Chapters)", "price": 499.0},
    "history": {"name": "Modern History (Spectrum)", "price": 299.0},
    "history_ancient": {"name": "Ancient History (R.S. Sharma)", "price": 299.0},
    "economy": {"name": "Economy for UPSC 2026", "price": 499.0},
    "environment": {"name": "Environment & Ecology", "price": 399.0},
    "scitech": {"name": "Science & Technology", "price": 399.0},
    "full_upsc": {"name": "Full UPSC Bundle (All Subjects)", "price": 2499.0},
    "geography_polity": {"name": "Geography + Polity Bundle", "price": 798.0},
    "geography_history": {"name": "Geography + History Bundle", "price": 748.0},
    # Meditation
    "meditation_l2": {"name": "Meditation Level 2", "price": 1499.0},
    "meditation_l3": {"name": "Meditation Level 3", "price": 1999.0},
    "meditation_l4": {"name": "Meditation Level 4", "price": 2499.0},
    "meditation_bundle": {"name": "Complete Meditation Journey", "price": 5999.0},
    # Graphotherapy
    "grapho_l2": {"name": "Graphotherapy Level 2", "price": 5000.0},
    "grapho_l3": {"name": "Graphotherapy Level 3", "price": 5000.0},
    "grapho_l4": {"name": "Graphotherapy Level 4", "price": 5000.0},
}


class OrderRequest(BaseModel):
    tier: str = None  # Legacy
    subject_id: str = None  # Generic product ID


class SubjectAccessResponse(BaseModel):
    user_id: int
    email: str
    purchased_subjects: List[str]


@router.get("/access", response_model=SubjectAccessResponse)
def get_user_access(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    purchased = current_user.purchased_subjects or []
    if current_user.is_premium or current_user.is_batch1_authorized or "full_upsc" in purchased:
        purchased = list(SUBJECT_PRODUCTS.keys())
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "purchased_subjects": purchased,
    }


@router.post("/create-order")
def create_order(
    request: OrderRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    subject_id = request.subject_id
    tier = request.tier

    if subject_id and subject_id in SUBJECT_PRODUCTS:
        product = SUBJECT_PRODUCTS[subject_id]
        amount = product["price"]
        
        # Determine prefix for webhook handling
        if "meditation" in subject_id:
            note = f"MEDITATION:{subject_id}"
        elif "grapho" in subject_id:
            note = f"GRAPHO:{subject_id}"
        else:
            note = f"SUBJECT:{subject_id}"
            
    elif tier == "premium":
        amount = 1500.0
        note = "TIER:premium"
    else:
        raise HTTPException(status_code=400, detail="Invalid product.")

    try:
        customer_details = {
            "customer_id": str(current_user.id),
            "customer_email": current_user.email,
            "customer_phone": getattr(current_user, "phone", "9999999999") or "9999999999",
            "customer_name": getattr(current_user, "full_name", "User") or "User"
        }

        # Redirect URL for Cashfree
        return_url = f"{FRONTEND_URL}/student/payment/status?order_id={{order_id}}"

        cashfree_order = cashfree_service.create_order(
            order_amount=amount,
            order_currency="INR",
            customer_details=customer_details,
            order_note=note,
            order_meta={"return_url": return_url}
        )
        return cashfree_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{order_id}")
def verify_payment(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """
    Proactively verify payment status with Cashfree.
    Used by the frontend status page to confirm unlock.
    """
    try:
        cf_order = cashfree_service.fetch_order_details(order_id)
        order_status = cf_order.get("order_status")
        order_note = cf_order.get("order_note", "")

        if order_status == "PAID":
            # Proactively unlock even if webhook is delayed
            _unlock_from_note(current_user, order_note, db)
            return {"status": "success", "order_status": order_status}
        
        return {"status": "pending", "order_status": order_status}
    except Exception as e:
        print(f"Verification Error: {e}")
        return {"status": "failed", "error": str(e)}


@router.post("/webhook")
async def cashfree_webhook(request: Request, db: Session = Depends(deps.get_db)):
    try:
        raw_body = await request.body()
        signature = request.headers.get("x-webhook-signature")
        timestamp = request.headers.get("x-webhook-timestamp")

        if not cashfree_service.verify_webhook_signature(signature, timestamp, raw_body.decode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid signature")

        event = json.loads(raw_body)
        if event.get("type") == "PAYMENT_SUCCESS_WEBHOOK":
            data = event.get("data", {})
            order = data.get("order", {})
            order_id = order.get("order_id", "")
            order_note = order.get("order_note", "")

            parts = order_id.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                user_id = int(parts[1])
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    _unlock_from_note(user, order_note, db)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _unlock_from_note(user: User, note: str, db: Session):
    if note.startswith("SUBJECT:"):
        subject_id = note.replace("SUBJECT:", "").strip()
        existing = list(user.purchased_subjects or [])
        if subject_id not in existing:
            existing.append(subject_id)
            user.purchased_subjects = existing
        user.is_batch1_authorized = True
        if subject_id == "full_upsc":
            user.is_premium = True

    elif note.startswith("MEDITATION:"):
        prod_id = note.replace("MEDITATION:", "").strip()
        progress = db.query(MeditationProgress).filter(MeditationProgress.user_id == user.id).first()
        if not progress:
            progress = MeditationProgress(user_id=user.id, unlocked_levels=1)
            db.add(progress)
        
        if prod_id == "meditation_l2": progress.unlocked_levels = max(progress.unlocked_levels, 2)
        elif prod_id == "meditation_l3": progress.unlocked_levels = max(progress.unlocked_levels, 3)
        elif prod_id == "meditation_l4": progress.unlocked_levels = max(progress.unlocked_levels, 4)
        elif "bundle" in prod_id: progress.unlocked_levels = 4

    elif note.startswith("GRAPHO:"):
        prod_id = note.replace("GRAPHO:", "").strip()
        progress = db.query(GraphotherapyProgress).filter(GraphotherapyProgress.user_id == user.id).first()
        if not progress:
            progress = GraphotherapyProgress(user_id=user.id, current_level=1)
            db.add(progress)
            
        if "l2" in prod_id: progress.current_level = max(progress.current_level, 2)
        elif "l3" in prod_id: progress.current_level = max(progress.current_level, 3)
        elif "l4" in prod_id: progress.current_level = max(progress.current_level, 4)

    elif note == "TIER:premium":
        user.is_premium = True

    db.commit()
