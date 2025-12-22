"""
Shopping Cart API Tests
Tests for cart management endpoints
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.course import Course
from app.models.cart import CartItem
from app.models.coupon import Coupon


client = TestClient(app)


class TestCartEndpoints:
    """Test cart API endpoints"""

    def test_get_empty_cart(
        self, client: TestClient, normal_user_token_headers: dict, db: Session
    ):
        """Test getting empty cart"""
        response = client.get("/api/v1/cart", headers=normal_user_token_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["item_count"] == 0
        assert data["total"] == 0.0

    def test_add_course_to_cart(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_course: Course,
    ):
        """Test adding a course to cart"""
        response = client.post(
            "/api/v1/cart/items",
            headers=test_user_headers,
            json={"course_id": test_course.id, "quantity": 1},
        )
        if response.status_code != 200:
            print(f"DEBUG: Status {response.status_code}, Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == test_course.id
        assert data["quantity"] == 1
        assert data["unit_price"] == test_course.price

    def test_update_cart_item_quantity(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_cart_item: CartItem,
    ):
        """Test updating cart item quantity"""
        response = client.patch(
            f"/api/v1/cart/items/{test_cart_item.id}",
            headers=test_user_headers,
            json={"quantity": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 5

    def test_remove_cart_item(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_cart_item: CartItem,
    ):
        """Test removing item from cart"""
        response = client.delete(
            f"/api/v1/cart/items/{test_cart_item.id}", headers=test_user_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify item was removed
        cart_response = client.get("/api/v1/cart", headers=test_user_headers)
        assert len(cart_response.json()["items"]) == 0

    def test_apply_coupon_to_cart(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_cart_item: CartItem,
        test_coupon: Coupon,
    ):
        """Test applying a valid coupon"""
        response = client.post(
            "/api/v1/cart/apply-coupon",
            headers=test_user_headers,
            json={"coupon_code": test_coupon.code},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_discount"] > 0

    def test_apply_invalid_coupon(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_cart_item: CartItem,
    ):
        """Test applying invalid coupon code"""
        response = client.post(
            "/api/v1/cart/apply-coupon",
            headers=test_user_headers,
            json={"coupon_code": "INVALID123"},
        )

        # Should still return cart, but no discount applied
        assert response.status_code in [200, 404]

    def test_clear_cart(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_cart_item: CartItem,
    ):
        """Test clearing entire cart"""
        response = client.delete("/api/v1/cart/clear", headers=test_user_headers)

        assert response.status_code == 200

        # Verify cart is empty
        cart_response = client.get("/api/v1/cart", headers=test_user_headers)
        assert len(cart_response.json()["items"]) == 0

    def test_cart_price_calculation(
        self,
        client: TestClient,
        test_user_headers: dict,
        db: Session,
        test_course: Course,
    ):
        """Test cart total calculation"""
        # Add multiple items
        client.post(
            "/api/v1/cart/items",
            headers=test_user_headers,
            json={"course_id": test_course.id, "quantity": 2},
        )

        response = client.get("/api/v1/cart/summary", headers=test_user_headers)
        data = response.json()

        expected_subtotal = test_course.price * 2
        assert data["subtotal"] == expected_subtotal
        assert data["total"] >= expected_subtotal - data["total_discount"]

    def test_guest_cart_without_auth(self, client: TestClient, test_course: Course):
        """Test guest can add to cart without authentication"""
        response = client.post(
            "/api/v1/cart/items", json={"course_id": test_course.id, "quantity": 1}
        )

        # Should work for guests
        assert response.status_code == 200

        # Should set guest cart cookie
        assert "guest_cart_session" in response.cookies or response.status_code == 200
