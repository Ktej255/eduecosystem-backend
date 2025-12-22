"""
Coupon & Discount Models
Supports percentage and fixed amount discounts with usage limits
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)

    # Coupon details
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "WELCOME20"
    description = Column(Text, nullable=True)

    # Discount configuration
    discount_type = Column(String, nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(Float, nullable=False)  # 20 for 20% or 500 for ₹500

    # Restrictions
    min_purchase_amount = Column(Float, nullable=True, default=0)  # Minimum order value
    max_discount_amount = Column(Float, nullable=True)  # Cap for percentage discounts

    # Course restrictions (null = all courses)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    # Creator
    instructor_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Usage limits
    usage_limit = Column(Integer, nullable=True)  # null = unlimited
    usage_count = Column(Integer, default=0, nullable=False)
    usage_per_user_limit = Column(Integer, default=1, nullable=False)  # Usually 1

    # Validity period
    valid_from = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])
    course = relationship("Course", foreign_keys=[course_id])
    usages = relationship(
        "CouponUsage", back_populates="coupon", cascade="all, delete-orphan"
    )


class CouponUsage(Base):
    """Track coupon usage for analytics and limits"""

    __tablename__ = "coupon_usages"

    id = Column(Integer, primary_key=True, index=True)

    coupon_id = Column(
        Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    payment_id = Column(
        Integer, ForeignKey("course_payments.id", ondelete="SET NULL"), nullable=True
    )

    # Discount details at time of use
    original_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)

    # Timestamp
    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User")
    payment = relationship("CoursePayment")
