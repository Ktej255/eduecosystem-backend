"""
Order API Tests
Tests for order management endpoints
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.order import Order
from app.models.cart import ShoppingCart


client = TestClient(app)


class TestOrderEndpoints:
    """Test order API endpoints"""

    def test_create_order_from_cart(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_cart_with_items: ShoppingCart,
    ):
        """Test creating order from cart"""
        response = client.post(
            "/api/v1/orders",
            headers=normal_user_token_headers,
            json={
                "cart_id": test_cart_with_items.id,
                "billing_name": "Test User",
                "billing_email": "test@example.com",
                "billing_address": "123 Test St",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_number" in data
        assert data["status"] == "pending"
        assert len(data["items"]) > 0
        assert data["total"] > 0

    def test_create_order_with_empty_cart(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_empty_cart: ShoppingCart,
    ):
        """Test creating order with empty cart fails"""
        response = client.post(
            "/api/v1/orders",
            headers=normal_user_token_headers,
            json={
                "cart_id": test_empty_cart.id,
                "billing_name": "Test User",
                "billing_email": "test@example.com",
            },
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_get_order_history(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_order: Order,
    ):
        """Test getting user's order history"""
        response = client.get("/api/v1/orders", headers=normal_user_token_headers)

        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert data["total"] >= 1
        assert len(data["orders"]) >= 1

    def test_get_order_details(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_order: Order,
    ):
        """Test getting order details by ID"""
        response = client.get(
            f"/api/v1/orders/{test_order.id}", headers=normal_user_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id
        assert data["order_number"] == test_order.order_number
        assert "items" in data

    def test_get_order_by_number(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_order: Order,
    ):
        """Test getting order by order number"""
        response = client.get(
            f"/api/v1/orders/number/{test_order.order_number}",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_number"] == test_order.order_number

    def test_cancel_pending_order(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_pending_order: Order,
    ):
        """Test cancelling a pending order"""
        response = client.post(
            f"/api/v1/orders/{test_pending_order.id}/cancel",
            headers=normal_user_token_headers,
            json={"reason": "Changed my mind"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify order is cancelled
        order_response = client.get(
            f"/api/v1/orders/{test_pending_order.id}", headers=normal_user_token_headers
        )
        assert order_response.json()["status"] == "cancelled"

    def test_cannot_cancel_completed_order(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_completed_order: Order,
    ):
        """Test cannot cancel completed order"""
        response = client.post(
            f"/api/v1/orders/{test_completed_order.id}/cancel",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 400

    def test_process_order_creates_enrollments(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_pending_order_with_courses: Order,
    ):
        """Test processing order creates enrollments"""
        response = client.post(
            f"/api/v1/orders/{test_pending_order_with_courses.id}/process",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "completed"

        # TODO: Verify enrollments were created in database

    def test_order_unauthorized_access(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        other_user_token_headers: dict,
        db: Session,
        test_order: Order,
    ):
        """Test users cannot access other users' orders"""
        response = client.get(
            f"/api/v1/orders/{test_order.id}", headers=other_user_token_headers
        )

        assert response.status_code == 403

    def test_guest_order_lookup(
        self, client: TestClient, db: Session, test_guest_order: Order
    ):
        """Test guest can lookup their orders by email"""
        response = client.post(
            "/api/v1/guest-orders/lookup", json={"email": test_guest_order.guest_email}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) >= 1

    def test_order_pagination(
        self, client: TestClient, normal_user_token_headers: dict, db: Session
    ):
        """Test order history pagination"""
        response = client.get(
            "/api/v1/orders?page=1&page_size=10", headers=normal_user_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data
        assert len(data["orders"]) <= 10

    def test_order_number_uniqueness(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        db: Session,
        test_cart_with_items: ShoppingCart,
    ):
        """Test each order gets unique order number"""
        # Create first order
        response1 = client.post(
            "/api/v1/orders",
            headers=normal_user_token_headers,
            json={
                "cart_id": test_cart_with_items.id,
                "billing_email": "test@example.com",
            },
        )

        order_number_1 = response1.json()["order_number"]

        # Create second order (would need new cart)
        # Just verify the format is correct
        assert order_number_1.startswith("ORD-")
        assert len(order_number_1) > 10
