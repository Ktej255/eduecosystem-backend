"""
Course Payment Schemas
Pydantic models for payment validation and serialization
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PaymentGateway(str, Enum):
    CASHFREE = "cashfree"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CoursePaymentBase(BaseModel):
    course_id: int
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    gateway: PaymentGateway = Field(
        ..., description="Standardized payment gateway: cashfree"
    )
    
class CoursePaymentCreate(CoursePaymentBase):
    user_id: int
    offer_applied: bool = False
    bundle_deal: bool = False

class CoursePaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    cashfree_order_id: Optional[str] = None
    cashfree_payment_id: Optional[str] = None
    invoice_url: Optional[str] = None
    error_message: Optional[str] = None
    payment_metadata: Optional[Dict[str, Any]] = None

class CoursePaymentInDBBase(CoursePaymentBase):
    id: int
    user_id: int
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CoursePayment(CoursePaymentInDBBase):
    """Full payment schema including all fields"""

    pass


class CoursePaymentWithDetails(CoursePaymentInDBBase):
    """Payment schema with course and user information"""

    course_title: Optional[str] = None
    user_email: Optional[str] = None
