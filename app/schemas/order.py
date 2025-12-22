"""
Order Schemas
Pydantic models for order validation and serialization
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class OrderItemCreate(BaseModel):
    """Schema for creating order item (internal use)"""

    course_id: Optional[int] = None
    bundle_id: Optional[int] = None
    item_name: str
    item_description: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(..., ge=0)
    discount: float = Field(default=0.0, ge=0)
    total: float = Field(..., ge=0)
    coupon_code: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Response schema for order item"""

    id: int
    order_id: int
    course_id: Optional[int] = None
    bundle_id: Optional[int] = None
    item_name: str
    item_description: Optional[str] = None
    quantity: int
    unit_price: float
    discount: float
    total: float
    coupon_code: Optional[str] = None
    created_at: datetime

    # Related object details
    course_thumbnail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Schema for creating an order from cart"""

    cart_id: int
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    customer_notes: Optional[str] = None


class OrderUpdate(BaseModel):
    """Schema for updating order"""

    status: Optional[str] = None
    admin_notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Full order response"""

    id: int
    order_number: str
    user_id: Optional[int] = None
    guest_email: Optional[str] = None
    status: str
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    customer_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderSummary(BaseModel):
    """Order summary (compact version)"""

    id: int
    order_number: str
    status: str
    total: float
    currency: str
    item_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Paginated order list"""

    orders: List[OrderSummary] = []
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class GuestOrderLookup(BaseModel):
    """Schema for looking up guest orders"""

    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    order_number: Optional[str] = None
