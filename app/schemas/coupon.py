"""
Cou

pon & Discount Schemas
Request/Response models for coupon API
"""

from pydantic import BaseModel, field_validator, ConfigDict, ValidationInfo
from typing import Optional
from datetime import datetime


class CouponBase(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str  # 'percentage' or 'fixed'
    discount_value: float
    min_purchase_amount: Optional[float] = 0
    max_discount_amount: Optional[float] = None
    course_id: Optional[int] = None
    category_id: Optional[int] = None
    usage_limit: Optional[int] = None
    usage_per_user_limit: int = 1
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: str) -> str:
        if v not in ["percentage", "fixed"]:
            raise ValueError('discount_type must be "percentage" or "fixed"')
        return v

    @field_validator("discount_value")
    @classmethod
    def validate_discount_value(cls, v: float, info: ValidationInfo) -> float:
        if v <= 0:
            raise ValueError("discount_value must be positive")
        if info.data.get("discount_type") == "percentage" and v > 100:
            raise ValueError("percentage discount cannot exceed 100%")
        return v


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    usage_limit: Optional[int] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class Coupon(CouponBase):
    id: int
    instructor_id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CouponValidationRequest(BaseModel):
    code: str
    course_id: int
    original_price: float


class CouponValidationResponse(BaseModel):
    valid: bool
    message: str
    discount_amount: Optional[float] = None
    final_price: Optional[float] = None
    coupon: Optional[Coupon] = None


class CouponUsageStats(BaseModel):
    total_uses: int
    total_discount_given: float
    total_revenue: float
    unique_users: int
    average_discount: float
