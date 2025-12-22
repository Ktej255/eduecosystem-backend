from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.utils import random_email, random_lower_string
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from unittest.mock import patch, MagicMock


def test_subscription_lifecycle_integration(client: TestClient, db: Session):
    # 1. Create a user
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, full_name="Sub Test User")
    user = crud_user.create(db, obj_in=user_in)

    # Login
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    auth_header = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 2. Create a Plan (Admin)
    from app.models.subscription import SubscriptionPlan

    plan = SubscriptionPlan(
        name="Test Plan",
        slug="test-plan",
        monthly_price=10.00,
        stripe_price_id_monthly="price_test_123",
        features="Feature 1, Feature 2",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # 3. Subscribe
    # Use /subscribe endpoint
    with patch(
        "app.services.subscription_service.stripe"
    ) as mock_stripe:
        # Mock Stripe subscription creation
        mock_stripe.Subscription.create.return_value = MagicMock(id="sub_123")
        
        r = client.post(
            f"{settings.API_V1_STR}/subscriptions/subscribe",
            params={"plan_id": plan.id, "billing_cycle": "monthly"},
            headers=auth_header,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "active"
        assert data["plan_id"] == plan.id

    # 4. Verify Access
    r = client.get(f"{settings.API_V1_STR}/subscriptions/me", headers=auth_header)
    assert r.status_code == 200
    sub_data = r.json()
    assert sub_data["status"] == "active"
    assert sub_data["plan_id"] == plan.id

    # 5. Cancel Subscription
    with patch(
        "app.services.subscription_service.stripe"
    ) as mock_stripe:
        # Mock Stripe subscription modification (cancel)
        mock_stripe.Subscription.modify.return_value = MagicMock(cancel_at_period_end=True)

        r = client.post(
            f"{settings.API_V1_STR}/subscriptions/cancel", headers=auth_header
        )
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled" or r.json()["cancel_at_period_end"] is True

    # 6. Verify Cancellation Status
    r = client.get(f"{settings.API_V1_STR}/subscriptions/me", headers=auth_header)
    assert r.status_code == 200
    # Depending on implementation, status might be 'cancelled' or 'active' with cancel_at_period_end=True
    # The service implementation sets status='cancelled' if immediate=True, else sets cancel_at_period_end=True
    # The default for cancel endpoint is immediate=False
    assert r.json()["cancel_at_period_end"] is True
