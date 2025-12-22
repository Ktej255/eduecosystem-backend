"""
Shopping Cart Models
Supports multi-item carts for both authenticated users and guest sessions
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ShoppingCart(Base):
    """
    Shopping cart for users and guests.
    Supports multiple items, coupons, and guest sessions.
    """

    __tablename__ = "shopping_carts"

    id = Column(Integer, primary_key=True, index=True)

    # User relationship (nullable for guest carts)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Guest session (for non-authenticated users)
    session_id = Column(String(100), unique=True, index=True, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For guest carts

    # Cart status
    is_active = Column(
        Integer, default=1
    )  # Using Integer instead of Boolean for SQLite compatibility

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ShoppingCart(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"


class CartItem(Base):
    """
    Individual items in a shopping cart.
    Can be courses or bundles with price snapshots and optional coupons.
    """

    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(
        Integer,
        ForeignKey("shopping_carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item type and ID (either course or bundle)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True
    )
    bundle_id = Column(
        Integer, ForeignKey("course_bundles.id", ondelete="CASCADE"), nullable=True
    )

    # Quantity (typically 1 for digital products, but flexible)
    quantity = Column(Integer, default=1, nullable=False)

    # Price snapshot (stored at time of adding to cart)
    unit_price = Column(Float, nullable=False)

    # Optional coupon for this item
    coupon_id = Column(
        Integer, ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True
    )
    discount_amount = Column(Float, default=0.0)

    # Timestamps
    added_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cart = relationship("ShoppingCart", back_populates="items")
    course = relationship("Course", foreign_keys=[course_id])
    bundle = relationship("CourseBundle", foreign_keys=[bundle_id])
    coupon = relationship("Coupon", foreign_keys=[coupon_id])

    def __repr__(self):
        item_type = "course" if self.course_id else "bundle"
        item_id = self.course_id or self.bundle_id
        return f"<CartItem(id={self.id}, {item_type}_id={item_id}, quantity={self.quantity})>"

    @property
    def subtotal(self):
        """Calculate subtotal before discount"""
        return self.unit_price * self.quantity

    @property
    def total(self):
        """Calculate total after discount"""
        return max(0, self.subtotal - self.discount_amount)
