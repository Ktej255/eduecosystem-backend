"""
Guest Session Service

Manages guest user sessions for checkout without account creation.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import secrets
import hashlib

from app.models.cart import ShoppingCart
from app.models.order import Order


class GuestService:
    """Service for managing guest checkout sessions"""

    @staticmethod
    def create_guest_session() -> str:
        """
        Create a unique guest session ID.

        Returns:
            Session ID string
        """
        # Generate secure random session ID
        random_bytes = secrets.token_bytes(32)
        session_id = hashlib.sha256(random_bytes).hexdigest()
        return f"guest-{session_id[:32]}"

    @staticmethod
    def get_or_create_guest_cart(
        db: Session, session_id: Optional[str] = None
    ) -> tuple[ShoppingCart, str]:
        """
        Get existing guest cart or create new one.

        Args:
            db: Database session
            session_id: Optional guest session ID

        Returns:
            Tuple of (cart, session_id)
        """
        if session_id:
            # Try to find existing cart
            cart = (
                db.query(ShoppingCart)
                .filter(
                    ShoppingCart.session_id == session_id, ShoppingCart.is_active == 1
                )
                .first()
            )

            if cart:
                # Check if cart hasn't expired (7 days)
                if cart.expires_at and cart.expires_at > datetime.utcnow():
                    return cart, session_id

        # Create new session and cart
        new_session_id = GuestService.create_guest_session()
        expires_at = datetime.utcnow() + timedelta(days=7)

        cart = ShoppingCart(
            session_id=new_session_id, expires_at=expires_at, is_active=1
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart, new_session_id

    @staticmethod
    def verify_guest_order_access(
        db: Session, order_id: int, email: str, order_number: Optional[str] = None
    ) -> Optional[Order]:
        """
        Verify guest has access to order by email.

        Args:
            db: Database session
            order_id: Order ID
            email: Guest email
            order_number: Optional order number for additional verification

        Returns:
            Order if access granted, None otherwise
        """
        query = db.query(Order).filter(Order.id == order_id, Order.guest_email == email)

        if order_number:
            query = query.filter(Order.order_number == order_number)

        return query.first()

    @staticmethod
    def convert_guest_to_user(db: Session, guest_email: str, user_id: int) -> int:
        """
        Convert guest orders to user account.

        Args:
            db: Database session
            guest_email: Guest email address
            user_id: New user ID to assign orders to

        Returns:
            Number of orders converted
        """
        # Find all guest orders with this email
        guest_orders = (
            db.query(Order)
            .filter(Order.guest_email == guest_email, Order.user_id.is_(None))
            .all()
        )

        # Assign to user
        count = 0
        for order in guest_orders:
            order.user_id = user_id
            order.guest_email = None  # Clear guest email since now linked to user
            count += 1

        db.commit()

        return count

    @staticmethod
    def merge_guest_cart_to_user(db: Session, session_id: str, user_id: int) -> bool:
        """
        Merge guest cart items into user's cart.

        Args:
            db: Database session
            session_id: Guest session ID
            user_id: User ID to merge into

        Returns:
            True if successful
        """
        # Get guest cart
        guest_cart = (
            db.query(ShoppingCart)
            .filter(ShoppingCart.session_id == session_id, ShoppingCart.is_active == 1)
            .first()
        )

        if not guest_cart or not guest_cart.items:
            return False

        # Get or create user cart
        user_cart = (
            db.query(ShoppingCart)
            .filter(ShoppingCart.user_id == user_id, ShoppingCart.is_active == 1)
            .first()
        )

        if not user_cart:
            user_cart = ShoppingCart(user_id=user_id, is_active=1)
            db.add(user_cart)
            db.flush()

        # Move items from guest cart to user cart
        for item in guest_cart.items:
            # Check if item already in user cart
            existing = next(
                (
                    i
                    for i in user_cart.items
                    if i.course_id == item.course_id and i.bundle_id == item.bundle_id
                ),
                None,
            )

            if not existing:
                # Transfer item
                item.cart_id = user_cart.id
            # If already exists, we just skip (don't duplicate)

        # Deactivate guest cart
        guest_cart.is_active = 0

        db.commit()

        return True

    @staticmethod
    def get_guest_order_summary(db: Session, email: str) -> Dict:
        """
        Get summary of guest orders by email.

        Args:
            db: Database session
            email: Guest email

        Returns:
            Summary dict with order count and total spent
        """
        orders = db.query(Order).filter(Order.guest_email == email).all()

        total_spent = sum(order.total for order in orders)

        return {
            "order_count": len(orders),
            "total_spent": float(total_spent),
            "orders": orders,
        }
