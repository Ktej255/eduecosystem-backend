"""
Shopping Cart Schemas
Pydantic models for cart validation and serialization
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime


class CartItemCreate(BaseModel):
    """Schema for adding item to cart"""

    course_id: Optional[int] = None
    bundle_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def validate_item_type(self):
        if not self.course_id and not self.bundle_id:
            raise ValueError("Either course_id or bundle_id must be provided")
        if self.course_id and self.bundle_id:
            raise ValueError("Cannot specify both course_id and bundle_id")
        return self


class CartItemUpdate(BaseModel):
    """Schema for updating cart item"""

    quantity: Optional[int] = Field(None, ge=1, le=100)
    coupon_code: Optional[str] = None


class ApplyCouponRequest(BaseModel):
    """Schema for applying coupon to cart"""

    coupon_code: str = Field(..., min_length=1, max_length=50)
    cart_item_id: Optional[int] = None  # If None, apply to entire cart


class CartItemResponse(BaseModel):
    """Response schema for cart item with details"""

    id: int
    cart_id: int
    course_id: Optional[int] = None
    bundle_id: Optional[int] = None
    quantity: int
    unit_price: float
    discount_amount: float
    subtotal: float
    total: float
    added_at: datetime

    # Related object details
    course_title: Optional[str] = None
    course_thumbnail: Optional[str] = None
    bundle_name: Optional[str] = None
    coupon_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartSummary(BaseModel):
    """Cart summary with totals"""

    cart_id: int
    items: List[CartItemResponse] = []
    item_count: int = 0
    subtotal: float = 0.0
    total_discount: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    currency: str = "INR"

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Full cart response"""

    id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[CartItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CartTotals(BaseModel):
    """Cart totals calculation"""

    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str = "INR"
    items_count: int
