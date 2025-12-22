"""
Course Payment Schemas
Pydantic models for payment validation and serialization
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CoursePaymentBase(BaseModel):
    """Base schema for course payments"""

    amount: float = Field(..., ge=0, description="Payment amount")
    currency: str = Field(default="INR", max_length=3)
    payment_provider: str = Field(
        ..., description="Payment gateway: stripe, razorpay, instamojo"
    )
    payment_method: Optional[str] = Field(
        None, description="Payment method used (card, paypal, etc)"
    )


class CoursePaymentCreate(CoursePaymentBase):
    """Schema for creating a new payment record"""

    course_id: int
    status: str = Field(default="pending", description="Payment status")

    # Optional provider-specific fields
    stripe_checkout_session_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    instamojo_payment_request_id: Optional[str] = None


class CoursePaymentUpdate(BaseModel):
    """Schema for updating payment status"""

    status: Optional[str] = Field(
        None, description="pending, succeeded, failed, refunded"
    )

    # Provider-specific IDs
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    instamojo_payment_id: Optional[str] = None

    # Failure/refund details
    failure_reason: Optional[str] = None
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None

    # Enrollment link
    enrollment_id: Optional[int] = None


class CoursePaymentInDBBase(CoursePaymentBase):
    """Base schema for payment in database"""

    id: int
    user_id: int
    course_id: int
    status: str
    enrollment_id: Optional[int] = None

    # Provider-specific fields
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    instamojo_payment_request_id: Optional[str] = None
    instamojo_payment_id: Optional[str] = None

    # Metadata
    failure_reason: Optional[str] = None
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
