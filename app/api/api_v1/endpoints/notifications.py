from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any, Dict
from app.api.deps import get_db, get_current_user
from app.models.user import User
from pywebpush import webpush, WebPushException
import json
import os

router = APIRouter()

# VAPID Keys
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "jjuOWI_7reH1j3TPE1wV24UP70rVcE1W22M2DfK5gEY")
VAPID_CLAIMS = {
    "sub": "mailto:admin@eduecosystem.com"
}

@router.post("/subscribe", response_model=Dict[str, str])
def subscribe_notifications(
    subscription: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Save the user's WebPush subscription object.
    """
    current_user.push_subscription = subscription
    db.add(current_user)
    db.commit()
    return {"message": "Subscribed successfully"}

@router.post("/send", response_model=Dict[str, str])
def send_notification(
    message: str = Body(..., embed=True),
    target_user_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send a push notification to a specific user (Admin only).
    """
    # Create notification record (optional for history)
    # ...

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user or not target_user.push_subscription:
        raise HTTPException(status_code=404, detail="User not subscribed to notifications")

    try:
        webpush(
            subscription_info=target_user.push_subscription,
            data=json.dumps({"title": "Eduecosystem Nudge", "body": message}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as ex:
        # Check if expired
        if ex.response and ex.response.status_code == 410:
             target_user.push_subscription = None
             db.commit()
             raise HTTPException(status_code=410, detail="Subscription expired")
        raise HTTPException(status_code=500, detail=f"WebPush failed: {ex}")

    return {"message": "Notification sent"}
