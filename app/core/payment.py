import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user_id: int, user_email: str):
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.PREMIUM_PRICE_ID,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url="http://localhost:3000/premium/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:3000/premium",
            metadata={"user_id": str(user_id)},
        )
        return checkout_session
    except Exception as e:
        raise e


def create_portal_session(customer_id: str):
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="http://localhost:3000/settings",
        )
        return portal_session
    except Exception as e:
        raise e


def cancel_subscription(subscription_id: str):
    try:
        stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        return True
    except Exception as e:
        raise e


def get_subscription_status(customer_id: str):
    try:
        subscriptions = stripe.Subscription.list(
            customer=customer_id, status="all", limit=1
        )
        if subscriptions and subscriptions.data:
            return subscriptions.data[0].status
        return "inactive"
    except Exception:
        return "inactive"


def handle_checkout_session(session, db):
    from app.crud import user as crud_user

    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")

    if user_id:
        user = crud_user.user.get(db, id=int(user_id))
        if user:
            update_data = {
                "is_premium": True,
                "stripe_customer_id": customer_id,
                "subscription_status": "active",
            }
            crud_user.user.update(db, db_obj=user, obj_in=update_data)
