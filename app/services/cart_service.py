"""
Shopping Cart Service
Business logic for cart management
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid

from app.models.cart import ShoppingCart, CartItem
from app.models.course import Course
from app.models.bundle import CourseBundle
from app.models.coupon import Coupon
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartSummary,
    CartItemResponse,
)


class CartService:
    """Service for shopping cart operations"""

    GUEST_CART_EXPIRY_DAYS = 7

    @staticmethod
    def get_or_create_cart(
        db: Session, user_id: Optional[int] = None, session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Get or create a cart for user or guest session"""

        if user_id:
            # Get user's active cart
            cart = (
                db.query(ShoppingCart)
                .filter(ShoppingCart.user_id == user_id, ShoppingCart.is_active == 1)
                .first()
            )

            if not cart:
                cart = ShoppingCart(user_id=user_id, is_active=1)
                db.add(cart)
                db.commit()
                db.refresh(cart)
        else:
            # Guest cart
            if not session_id:
                session_id = str(uuid.uuid4())

            cart = (
                db.query(ShoppingCart)
                .filter(
                    ShoppingCart.session_id == session_id, ShoppingCart.is_active == 1
                )
                .first()
            )

            if not cart:
                cart = ShoppingCart(
                    session_id=session_id,
                    is_active=1,
                    expires_at=datetime.utcnow()
                    + timedelta(days=CartService.GUEST_CART_EXPIRY_DAYS),
                )
                db.add(cart)
                db.commit()
                db.refresh(cart)

        return cart

    @staticmethod
    def add_item(db: Session, cart_id: int, item_data: CartItemCreate) -> CartItem:
        """Add item to cart"""

        cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Get item price
        if item_data.course_id:
            course = db.query(Course).filter(Course.id == item_data.course_id).first()
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")

            # Check if already in cart
            existing_item = (
                db.query(CartItem)
                .filter(
                    CartItem.cart_id == cart_id,
                    CartItem.course_id == item_data.course_id,
                )
                .first()
            )

            if existing_item:
                # Update quantity
                existing_item.quantity += item_data.quantity
                existing_item.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_item)
                return existing_item

            unit_price = course.price

        elif item_data.bundle_id:
            bundle = (
                db.query(CourseBundle)
                .filter(CourseBundle.id == item_data.bundle_id)
                .first()
            )
            if not bundle:
                raise HTTPException(status_code=404, detail="Bundle not found")

            # Check if already in cart
            existing_item = (
                db.query(CartItem)
                .filter(
                    CartItem.cart_id == cart_id,
                    CartItem.bundle_id == item_data.bundle_id,
                )
                .first()
            )

            if existing_item:
                existing_item.quantity += item_data.quantity
                existing_item.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_item)
                return existing_item

            unit_price = bundle.price
        else:
            raise HTTPException(
                status_code=400, detail="Must specify course_id or bundle_id"
            )

        # Create new cart item
        cart_item = CartItem(
            cart_id=cart_id,
            course_id=item_data.course_id,
            bundle_id=item_data.bundle_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            discount_amount=0.0,
        )

        db.add(cart_item)
        cart.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cart_item)

        return cart_item

    @staticmethod
    def update_item(
        db: Session, cart_item_id: int, update_data: CartItemUpdate
    ) -> CartItem:
        """Update cart item quantity or apply coupon"""

        cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        if update_data.quantity is not None:
            cart_item.quantity = update_data.quantity

        if update_data.coupon_code:
            # Apply coupon
            CartService.apply_coupon_to_item(db, cart_item, update_data.coupon_code)

        cart_item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cart_item)

        return cart_item

    @staticmethod
    def remove_item(db: Session, cart_item_id: int) -> bool:
        """Remove item from cart"""

        cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        db.delete(cart_item)
        db.commit()

        return True

    @staticmethod
    def clear_cart(db: Session, cart_id: int) -> bool:
        """Clear all items from cart"""

        cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        db.commit()

        return True

    @staticmethod
    def apply_coupon_to_item(db: Session, cart_item: CartItem, coupon_code: str):
        """Apply coupon to a cart item"""

        coupon = (
            db.query(Coupon)
            .filter(Coupon.code == coupon_code, Coupon.is_active == True)
            .first()
        )

        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found or inactive")

        # Validate coupon
        now = datetime.utcnow()
        if coupon.valid_until and coupon.valid_until < now:
            raise HTTPException(status_code=400, detail="Coupon has expired")

        if coupon.valid_from and coupon.valid_from > now:
            raise HTTPException(status_code=400, detail="Coupon not yet valid")

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            raise HTTPException(status_code=400, detail="Coupon usage limit reached")

        # Check if coupon applies to this item
        if coupon.course_id and coupon.course_id != cart_item.course_id:
            raise HTTPException(
                status_code=400, detail="Coupon not valid for this course"
            )

        # Calculate discount
        if coupon.discount_type == "percentage":
            discount = (
                cart_item.unit_price * cart_item.quantity * coupon.discount_value
            ) / 100
            if coupon.max_discount_amount:
                discount = min(discount, coupon.max_discount_amount)
        else:  # fixed
            discount = coupon.discount_value

        # Check minimum purchase
        if (
            coupon.min_purchase_amount
            and (cart_item.unit_price * cart_item.quantity) < coupon.min_purchase_amount
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Minimum purchase amount of {coupon.min_purchase_amount} required",
            )

        cart_item.coupon_id = coupon.id
        cart_item.discount_amount = discount

    @staticmethod
    def get_cart_summary(db: Session, cart_id: int) -> CartSummary:
        """Get cart summary with totals"""

        cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()

        # Build item responses
        item_responses = []
        subtotal = 0.0
        total_discount = 0.0

        for item in items:
            # Get course or bundle details
            course_title = None
            course_thumbnail = None
            bundle_name = None
            coupon_code = None

            if item.course_id:
                course = db.query(Course).filter(Course.id == item.course_id).first()
                if course:
                    course_title = course.title
                    course_thumbnail = course.thumbnail_url

            if item.bundle_id:
                bundle = (
                    db.query(CourseBundle)
                    .filter(CourseBundle.id == item.bundle_id)
                    .first()
                )
                if bundle:
                    bundle_name = bundle.name

            if item.coupon_id:
                coupon = db.query(Coupon).filter(Coupon.id == item.coupon_id).first()
                if coupon:
                    coupon_code = coupon.code

            item_response = CartItemResponse(
                id=item.id,
                cart_id=item.cart_id,
                course_id=item.course_id,
                bundle_id=item.bundle_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                subtotal=item.subtotal,
                total=item.total,
                added_at=item.added_at,
                course_title=course_title,
                course_thumbnail=course_thumbnail,
                bundle_name=bundle_name,
                coupon_code=coupon_code,
            )

            item_responses.append(item_response)
            subtotal += item.subtotal
            total_discount += item.discount_amount

        # Calculate tax (you can customize this based on your tax rules)
        tax_amount = 0.0  # Implement tax calculation if needed

        total = subtotal - total_discount + tax_amount

        return CartSummary(
            cart_id=cart_id,
            items=item_responses,
            item_count=len(items),
            subtotal=subtotal,
            total_discount=total_discount,
            tax_amount=tax_amount,
            total=total,
            currency="INR",
        )
