"""
Guest Checkout API Endpoints

Endpoints for guest checkout, order tracking, and account conversion.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.api import deps
from app.models.user import User
from app.services.guest_service import GuestService
from app.services.order_service import OrderService

router = APIRouter()

GUEST_SESSION_COOKIE = "guest_session_id"


class GuestCheckoutRequest(BaseModel):
    """Guest checkout request"""

    email: EmailStr
    billing_name: str
    billing_address: Optional[str] = None


class GuestOrderTrackingRequest(BaseModel):
    """Guest order tracking request"""

    email: EmailStr
    order_number: str


class GuestConversionRequest(BaseModel):
    """Convert guest to user request"""

    guest_email: EmailStr


@router.post("/guest/cart/create")
def create_guest_cart(response: Response, db: Session = Depends(deps.get_db)):
    """
    Create a guest shopping cart session.
    Returns session ID to be stored in cookie.
    """
    cart, session_id = GuestService.get_or_create_guest_cart(db)

    # Set cookie
    response.set_cookie(
        key=GUEST_SESSION_COOKIE,
        value=session_id,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        samesite="lax",
    )

    return {"session_id": session_id, "cart_id": cart.id, "expires_at": cart.expires_at}


@router.post("/guest/checkout")
def guest_checkout(
    checkout_request: GuestCheckoutRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """
    Process guest checkout.
    Creates order without user account.
    """
    # Get guest session from cookie
    session_id = request.cookies.get(GUEST_SESSION_COOKIE)

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="No guest session found. Please add items to cart first.",
        )

    # Get guest cart
    cart, _ = GuestService.get_or_create_guest_cart(db, session_id)

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Create order with guest email
    # This would integrate with OrderService
    # For now, return mock response

    return {
        "status": "success",
        "message": "Order created",
        "order_number": "ORD-GUEST-12345",
        "tracking_info": {
            "email": checkout_request.email,
            "instructions": "Check your email for order confirmation and tracking link",
        },
    }


@router.post("/guest/track-order")
def track_guest_order(
    tracking_request: GuestOrderTrackingRequest, db: Session = Depends(deps.get_db)
):
    """
    Track guest order by email and order number.
    """
    # Get order by number
    order = OrderService.get_order_by_number(db, tracking_request.order_number)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify email matches
    if order.guest_email != tracking_request.email:
        raise HTTPException(status_code=404, detail="Order not found")

    # Return order details
    return OrderService.build_order_response(db, order)


@router.get("/guest/orders/{email}")
def get_guest_orders_by_email(email: str, db: Session = Depends(deps.get_db)):
    """
    Get all guest orders by email.
    Useful for "view all my orders" without login.
    """
    summary = GuestService.get_guest_order_summary(db, email)

    return {
        "email": email,
        "order_count": summary["order_count"],
        "total_spent": summary["total_spent"],
        "orders": [
            {
                "order_number": order.order_number,
                "status": order.status.value,
                "total": float(order.total),
                "created_at": order.created_at,
            }
            for order in summary["orders"]
        ],
    }


@router.post("/guest/convert-to-user")
def convert_guest_to_user(
    conversion_request: GuestConversionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Convert guest orders to user account.
    Called after user registers with email that has guest orders.
    """
    # Check if user's email matches guest email
    if current_user.email != conversion_request.guest_email:
        raise HTTPException(status_code=400, detail="Email does not match current user")

    # Convert guest orders
    converted_count = GuestService.convert_guest_to_user(
        db, conversion_request.guest_email, current_user.id
    )

    return {
        "status": "success",
        "message": f"Converted {converted_count} guest orders to your account",
        "orders_converted": converted_count,
    }


@router.post("/guest/merge-cart")
def merge_guest_cart(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Merge guest cart into user cart after login.
    """
    session_id = request.cookies.get(GUEST_SESSION_COOKIE)

    if not session_id:
        return {"status": "no_guest_cart", "message": "No guest cart to merge"}

    # Merge cart
    success = GuestService.merge_guest_cart_to_user(db, session_id, current_user.id)

    # Clear guest cookie
    response.delete_cookie(GUEST_SESSION_COOKIE)

    if success:
        return {"status": "success", "message": "Guest cart merged into your account"}
    else:
        return {"status": "no_items", "message": "No items in guest cart"}
