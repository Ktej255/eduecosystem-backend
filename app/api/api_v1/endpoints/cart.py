"""
Shopping Cart API Endpoints
Manage shopping carts for authenticated users and guest sessions
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.cart import ShoppingCart, CartItem
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartSummary,
    ApplyCouponRequest,
)
from app.services.cart_service import CartService

router = APIRouter()

GUEST_CART_COOKIE = "guest_cart_session"


@router.get("/cart", response_model=CartSummary)
def get_cart(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Get current cart for authenticated user or guest session.
    Returns cart summary with items and totals.
    """
    # Get or create cart
    if current_user:
        cart = CartService.get_or_create_cart(db, user_id=current_user.id)
    else:
        # Guest cart - use session cookie
        session_id = request.cookies.get(GUEST_CART_COOKIE)
        cart = CartService.get_or_create_cart(db, session_id=session_id)

        # Set cookie if new session
        if not session_id:
            response.set_cookie(
                key=GUEST_CART_COOKIE,
                value=cart.session_id,
                max_age=7 * 24 * 60 * 60,  # 7 days
                httponly=True,
            )

    return CartService.get_cart_summary(db, cart.id)


@router.post("/cart/items", response_model=CartItemResponse)
def add_to_cart(
    item_data: CartItemCreate,
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Add an item to the cart.
    Works for both authenticated users and guests.
    """
    # Get or create cart
    if current_user:
        cart = CartService.get_or_create_cart(db, user_id=current_user.id)
    else:
        session_id = request.cookies.get(GUEST_CART_COOKIE)
        cart = CartService.get_or_create_cart(db, session_id=session_id)

        if not session_id:
            response.set_cookie(
                key=GUEST_CART_COOKIE,
                value=cart.session_id,
                max_age=7 * 24 * 60 * 60,
                httponly=True,
            )

    # Add item to cart
    cart_item = CartService.add_item(db, cart.id, item_data)

    # Get full item details for response
    cart_summary = CartService.get_cart_summary(db, cart.id)
    item_response = next(
        (item for item in cart_summary.items if item.id == cart_item.id), None
    )

    if not item_response:
        raise HTTPException(status_code=500, detail="Failed to create cart item")

    return item_response


@router.patch("/cart/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    update_data: CartItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Update cart item quantity or apply coupon.
    """
    # Verify item belongs to user's cart
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_item.cart_id).first()

    # Verify ownership
    if current_user:
        if cart.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        # For guests, verify via cookie (handled by service)
        pass

    # Update item
    updated_item = CartService.update_item(db, item_id, update_data)

    # Get full details
    cart_summary = CartService.get_cart_summary(db, cart.id)
    item_response = next(
        (item for item in cart_summary.items if item.id == updated_item.id), None
    )

    return item_response


@router.delete("/cart/items/{item_id}")
def remove_from_cart(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Remove an item from the cart.
    """
    # Verify item belongs to user's cart
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_item.cart_id).first()

    # Verify ownership
    if current_user:
        if cart.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    CartService.remove_item(db, item_id)

    return {"status": "success", "message": "Item removed from cart"}


@router.delete("/cart/clear")
def clear_cart(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Clear all items from the cart.
    """
    # Get cart
    if current_user:
        cart = CartService.get_or_create_cart(db, user_id=current_user.id)
    else:
        session_id = request.cookies.get(GUEST_CART_COOKIE)
        if not session_id:
            raise HTTPException(status_code=404, detail="No cart found")
        cart = CartService.get_or_create_cart(db, session_id=session_id)

    CartService.clear_cart(db, cart.id)

    return {"status": "success", "message": "Cart cleared"}


@router.post("/cart/apply-coupon")
def apply_coupon(
    coupon_request: ApplyCouponRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Apply a coupon code to cart or specific cart item.
    """
    # Get cart
    if current_user:
        cart = CartService.get_or_create_cart(db, user_id=current_user.id)
    else:
        session_id = request.cookies.get(GUEST_CART_COOKIE)
        if not session_id:
            raise HTTPException(status_code=404, detail="No cart found")
        cart = CartService.get_or_create_cart(db, session_id=session_id)

    # Get items to apply coupon to
    if coupon_request.cart_item_id:
        # Apply to specific item
        cart_items = (
            db.query(CartItem)
            .filter(
                CartItem.id == coupon_request.cart_item_id, CartItem.cart_id == cart.id
            )
            .all()
        )

        if not cart_items:
            raise HTTPException(status_code=404, detail="Cart item not found")
    else:
        # Apply to all items
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

    # Apply coupon to each item
    for cart_item in cart_items:
        try:
            CartService.apply_coupon_to_item(db, cart_item, coupon_request.coupon_code)
        except HTTPException:
            # If coupon doesn't apply to this item, skip it
            continue

    db.commit()

    # Return updated cart summary
    return CartService.get_cart_summary(db, cart.id)


@router.get("/cart/summary", response_model=CartSummary)
def get_cart_summary(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
):
    """
    Get cart summary with totals (alias for GET /cart).
    """
    if current_user:
        cart = CartService.get_or_create_cart(db, user_id=current_user.id)
    else:
        session_id = request.cookies.get(GUEST_CART_COOKIE)
        if not session_id:
            # Return empty cart
            return CartSummary(
                cart_id=0,
                items=[],
                item_count=0,
                subtotal=0.0,
                total_discount=0.0,
                tax_amount=0.0,
                total=0.0,
                currency="INR",
            )
        cart = CartService.get_or_create_cart(db, session_id=session_id)

    return CartService.get_cart_summary(db, cart.id)
