"""
Payment Method Schemas

Pydantic schemas for payment method API.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class PaymentMethodCreate(BaseModel):
    """Schema for creating a payment method"""

    gateway: str = Field(..., description="Payment gateway (stripe, paypal, razorpay)")
    method_type: str = Field(
        ..., description="Payment method type (card, paypal, bank_account)"
    )
    gateway_token: str = Field(..., description="Gateway-specific token or ID")
    gateway_customer_id: Optional[str] = None
    display_name: Optional[str] = None
    last_four: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = Field(None, ge=1, le=12)
    expiry_year: Optional[int] = Field(None, ge=2024)
    paypal_email: Optional[str] = None
    is_default: bool = False


class PaymentMethodUpdate(BaseModel):
    """Schema for updating a payment method"""

    display_name: Optional[str] = None
    is_default: Optional[bool] = None


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response"""

    id: int
    gateway: str
    method_type: str
    display_name: Optional[str]
    last_four: Optional[str]
    card_brand: Optional[str]
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    paypal_email: Optional[str]
    is_default: bool
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
