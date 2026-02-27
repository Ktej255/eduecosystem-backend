import json
from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session
from app.models.push_subscription import PushSubscription
import os

# You must generate these VAPID keys using `webpush.generate_vapid_keypair()`
# and set them securely in your production `.env`
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "your_private_key_here")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "your_public_key_here")
VAPID_SUBJECT = "mailto:admin@eduecosystem.com"

class WebPushService:
    @staticmethod
    def send_push_notification(db: Session, user_id: int, payload: dict):
        """
        Retrieves all valid push subscriptions for a user and dispatches
        a push notification using the standard Web Push protocol.
        """
        subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
        success_count = 0
        
        for sub in subscriptions:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }
            
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_SUBJECT}
                )
                success_count += 1
            except WebPushException as ex:
                print(f"Web Push Error: {repr(ex)}")
                # If the subscription is expired/unsubscribed, we remove it.
                if ex.response and ex.response.status_code in [404, 410]:
                    print("Subscription expired, removing from DB.")
                    db.delete(sub)
            except Exception as e:
                print(f"Unexpected Web Push Error: {e}")
                
        db.commit()
        return success_count

webpush_service = WebPushService()
