"""
Order Models
Complete order management for eCommerce with support for multi-item purchases
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import random
import string

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""

    PENDING = "pending"  # Order created, awaiting payment
    PROCESSING = "processing"  # Payment received, processing enrollments
    COMPLETED = "completed"  # Order fully processed, enrollments created
    FAILED = "failed"  # Payment failed
    REFUNDED = "refunded"  # Order refunded
    CANCELLED = "cancelled"  # Order cancelled by user


class Order(Base):
    """
    Order model for multi-item purchases.
    Links cart to payment and tracks order lifecycle.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # Order identification
    order_number = Column(String(50), unique=True, index=True, nullable=False)

    # User relationship (nullable for guest orders)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    guest_email = Column(String(255), nullable=True, index=True)  # For guest orders

    # Cart reference (optional, cart might be deleted after order)
    cart_id = Column(
        Integer, ForeignKey("shopping_carts.id", ondelete="SET NULL"), nullable=True
    )

    # Order status
    status = Column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True
    )

    # Pricing
    subtotal = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), default="INR", nullable=False)

    # Billing information (snapshot)
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)

    # Payment reference
    payment_id = Column(
        Integer, ForeignKey("course_payments.id", ondelete="SET NULL"), nullable=True
    )

    # Notes and metadata
    customer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    cart = relationship("ShoppingCart", foreign_keys=[cart_id])
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payment = relationship("CoursePayment", foreign_keys=[payment_id])
    invoice = relationship("Invoice", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order(order_number={self.order_number}, status={self.status}, total={self.total})>"

    @staticmethod
    def generate_order_number() -> str:
        """Generate unique order number: ORD-{timestamp}-{random}"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        random_str = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        return f"ORD-{timestamp}-{random_str}"


class OrderItem(Base):
    """
    Individual items in an order.
    Snapshot of purchased courses or bundles at time of order.
    """

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Item type (course or bundle)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    bundle_id = Column(
        Integer, ForeignKey("course_bundles.id", ondelete="SET NULL"), nullable=True
    )

    # Snapshot data (stored at purchase time)
    item_name = Column(String(500), nullable=False)  # Course/bundle title
    item_description = Column(Text, nullable=True)

    # Pricing
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    total = Column(Float, nullable=False)

    # Coupon applied (if any)
    coupon_code = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order = relationship("Order", back_populates="items")
    course = relationship("Course", foreign_keys=[course_id])
    bundle = relationship("CourseBundle", foreign_keys=[bundle_id])

    def __repr__(self):
        return f"<OrderItem(id={self.id}, item={self.item_name}, total={self.total})>"
