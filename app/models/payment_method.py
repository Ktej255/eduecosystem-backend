"""
Payment Method Models

Stored payment methods for users (cards, PayPal, etc.)
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class PaymentGateway(str, enum.Enum):
    """Payment gateway enumeration"""

    STRIPE = "stripe"
    PAYPAL = "paypal"
    RAZORPAY = "razorpay"
    INSTAMOJO = "instamojo"


class PaymentMethodType(str, enum.Enum):
    """Payment method type enumeration"""

    CARD = "card"
    PAYPAL = "paypal"
    BANK_ACCOUNT = "bank_account"
    UPI = "upi"
    WALLET = "wallet"


class PaymentMethod(Base):
    """
    Saved payment methods for users.
    Stores tokenized payment method references from various gateways.
    """

    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Gateway and type
    gateway = Column(SQLEnum(PaymentGateway), nullable=False)
    method_type = Column(SQLEnum(PaymentMethodType), nullable=False)

    # Gateway-specific token/ID (encrypted in production)
    gateway_token = Column(String(255), nullable=False)
    gateway_customer_id = Column(String(255), nullable=True)  # Stripe customer ID, etc.

    # Display information
    display_name = Column(String(100), nullable=True)  # e.g., "Visa ending in 4242"
    last_four = Column(String(4), nullable=True)  # Last 4 digits of card
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, amex, etc.
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)

    # PayPal specific
    paypal_email = Column(String(255), nullable=True)

    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, user_id={self.user_id}, type={self.method_type}, gateway={self.gateway})>"

    @property
    def masked_number(self):
        """Get masked card number for display"""
        if self.last_four:
            return f"**** **** **** {self.last_four}"
        return None
