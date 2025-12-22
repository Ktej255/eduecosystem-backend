"""
Order API Endpoints
Manage orders, order history, and order processing
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderSummary,
    OrderListResponse,
    GuestOrderLookup,
)
from app.services.order_service import OrderService

router = APIRouter()

GUEST_CART_COOKIE = "guest_cart_session"


@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Create an order from shopping cart.
    Works for both authenticated users and guests.
    """
    # Determine user ID and guest email
    user_id = current_user.id if current_user else None
    guest_email = None

    if not current_user:
        # Guest order - require billing email
        if not order_data.billing_email:
            raise HTTPException(
                status_code=400, detail="Billing email is required for guest checkout"
            )
        guest_email = order_data.billing_email

    # Create order from cart
    order = OrderService.create_order_from_cart(
        db=db,
        cart_id=order_data.cart_id,
        order_data=order_data,
        user_id=user_id,
        guest_email=guest_email,
    )

    # Build response
    return OrderService.build_order_response(db, order)


@router.get("/orders", response_model=OrderListResponse)
def get_user_orders(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get authenticated user's order history with pagination.
    """
    skip = (page - 1) * page_size

    orders, total = OrderService.get_user_orders(
        db=db, user_id=current_user.id, skip=skip, limit=page_size
    )

    # Build order summaries
    order_summaries = []
    for order in orders:
        # Count items
        item_count = len(order.items)

        order_summary = OrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.status.value,
            total=order.total,
            currency=order.currency,
            item_count=item_count,
            created_at=order.created_at,
        )
        order_summaries.append(order_summary)

    return OrderListResponse(
        orders=order_summaries, total=total, page=page, page_size=page_size
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Get order details by ID.
    Accessible by order owner or guest with matching email.
    """
    order = OrderService.get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify access
    if current_user:
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to view this order"
            )
    else:
        # For guests, we can't verify without email - this endpoint requires auth for non-owners
        raise HTTPException(status_code=401, detail="Authentication required")

    return OrderService.build_order_response(db, order)


@router.get("/orders/number/{order_number}", response_model=OrderResponse)
def get_order_by_number(
    order_number: str,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Get order by order number.
    """
    order = OrderService.get_order_by_number(db, order_number)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify access
    if current_user:
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to view this order"
            )
    else:
        # Guest access allowed if email matches (checked in guest endpoint)
        raise HTTPException(status_code=401, detail="Authentication required")

    return OrderService.build_order_response(db, order)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Cancel a pending order.
    """
    order = OrderService.get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify ownership
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Cancel order
    cancelled_order = OrderService.cancel_order(db, order_id, reason)

    return {
        "status": "success",
        "message": "Order cancelled",
        "order_number": cancelled_order.order_number,
    }


@router.post("/guest-orders/lookup", response_model=OrderListResponse)
def lookup_guest_orders(
    lookup_data: GuestOrderLookup, db: Session = Depends(deps.get_db)
):
    """
    Look up guest orders by email.
    For guest users to track their orders.
    """
    if lookup_data.order_number:
        # Look up specific order
        order = OrderService.get_order_by_number(db, lookup_data.order_number)

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Verify email matches
        if order.guest_email != lookup_data.email:
            raise HTTPException(status_code=404, detail="Order not found")

        # Count items
        item_count = len(order.items)

        order_summary = OrderSummary(
            id=order.id,
            order_number=order.order_number,
            status=order.status.value,
            total=order.total,
            currency=order.currency,
            item_count=item_count,
            created_at=order.created_at,
        )

        return OrderListResponse(orders=[order_summary], total=1, page=1, page_size=1)
    else:
        # Look up all orders for email
        orders, total = OrderService.get_guest_orders(
            db=db,
            guest_email=lookup_data.email,
            skip=0,
            limit=50,  # Limit guest lookups
        )

        order_summaries = []
        for order in orders:
            item_count = len(order.items)

            order_summary = OrderSummary(
                id=order.id,
                order_number=order.order_number,
                status=order.status.value,
                total=order.total,
                currency=order.currency,
                item_count=item_count,
                created_at=order.created_at,
            )
            order_summaries.append(order_summary)

        return OrderListResponse(
            orders=order_summaries, total=total, page=1, page_size=50
        )


@router.post("/orders/{order_id}/process")
def process_order(
    order_id: int,
    payment_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Process order and create enrollments (internal use).
    Usually called after successful payment.
    """
    order = OrderService.get_order(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify ownership or admin
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    processed_order = OrderService.process_order(db, order_id, payment_id)

    return {
        "status": "success",
        "message": "Order processed",
        "order_number": processed_order.order_number,
        "order_status": processed_order.status.value,
    }
