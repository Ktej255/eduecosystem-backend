"""
Marketplace Schemas

Pydantic models for marketplace API requests and responses.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Revenue & Earnings ---


class InstructorEarnings(BaseModel):
    total_revenue: Decimal
    total_earnings: Decimal
    pending_payout: Decimal
    total_paid: Decimal
    available_balance: Decimal


class RevenueStats(BaseModel):
    total_revenue: Decimal
    platform_earnings: Decimal
    instructor_earnings: Decimal
    affiliate_commissions: Decimal
    total_sales: int
    average_sale_value: Decimal


class TransactionList(BaseModel):
    id: int
    amount: Decimal
    type: str
    date: datetime
    status: str


# --- Payouts ---


class PayoutRequest(BaseModel):
    amount: Optional[Decimal] = None
    payment_method: str = "stripe"


class PayoutResponse(BaseModel):
    id: int
    amount: Decimal
    status: str
    payment_method: str
    requested_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]
    failure_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# --- Bundles ---


class BundleCreate(BaseModel):
    title: str
    description: str
    course_ids: List[int]
    discount_percentage: Decimal
    slug: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_published: bool = False


class BundleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    discount_percentage: Optional[Decimal] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


class BundleCourseInfo(BaseModel):
    id: int
    title: str
    price: Decimal


class BundleResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str]
    price: Decimal
    original_price: Decimal
    discount_percentage: Decimal
    thumbnail_url: Optional[str]
    is_published: bool
    total_enrollments: int
    courses: List[BundleCourseInfo] = []

    model_config = ConfigDict(from_attributes=True)


# --- Subscriptions ---


class PlanCreate(BaseModel):
    name: str
    monthly_price: Decimal
    yearly_price: Optional[Decimal] = None
    description: Optional[str] = None
    features: List[str] = []
    access_level: str = "standard"
    trial_days: int = 0


class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    monthly_price: Decimal
    yearly_price: Optional[Decimal]
    description: Optional[str]
    features: Optional[str]  # JSON string
    trial_days: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    id: int
    plan_id: int
    status: str
    billing_cycle: str
    current_period_end: datetime
    cancel_at_period_end: bool
    plan: PlanResponse

    model_config = ConfigDict(from_attributes=True)


# --- Affiliates ---


class AffiliateRegister(BaseModel):
    custom_slug: Optional[str] = None
    payment_method: str = "paypal"
    payout_email: Optional[str] = None


class AffiliateStats(BaseModel):
    referral_code: str
    clicks: int
    conversions: int
    conversion_rate: float
    total_earnings: float
    pending_earnings: float
    paid_earnings: float


class AffiliateLinkResponse(BaseModel):
    referral_code: str
    tracking_cookie: str
