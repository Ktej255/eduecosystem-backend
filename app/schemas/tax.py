"""
Tax Schemas

Pydantic schemas for tax-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Tax Rate Schemas
class TaxRateBase(BaseModel):
    country_code: str = Field(
        ..., max_length=2, description="ISO 3166-1 alpha-2 country code"
    )
    state_code: Optional[str] = Field(None, max_length=10)
    region_name: str = Field(..., max_length=100)
    tax_name: str = Field(..., max_length=50, description="e.g., VAT, GST, Sales Tax")
    tax_rate: Decimal = Field(
        ..., ge=0, le=1, description="Tax rate as decimal (e.g., 0.20 for 20%)"
    )
    tax_type: str = Field(default="percentage", max_length=20)

    applies_to_digital_goods: bool = True
    applies_to_physical_goods: bool = True
    applies_to_services: bool = True
    applies_to_subscriptions: bool = True

    is_compound: bool = False
    compound_order: int = 0

    description: Optional[str] = None
    tax_id_required: bool = False

    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class TaxRateCreate(TaxRateBase):
    """Schema for creating a tax rate"""

    pass


class TaxRateUpdate(BaseModel):
    """Schema for updating a tax rate"""

    tax_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None
    applies_to_digital_goods: Optional[bool] = None
    applies_to_physical_goods: Optional[bool] = None
    applies_to_services: Optional[bool] = None
    applies_to_subscriptions: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    description: Optional[str] = None


class TaxRateResponse(TaxRateBase):
    """Schema for tax rate response"""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Tax Calculation Schemas
class TaxCalculationRequest(BaseModel):
    """Request schema for tax calculation"""

    subtotal: Decimal = Field(..., gt=0, description="Amount before tax")
    country_code: str = Field(..., max_length=2)
    state_code: Optional[str] = Field(None, max_length=10)
    product_type: str = Field(
        default="digital_goods",
        description="digital_goods, physical_goods, services, subscriptions",
    )
    is_inclusive: bool = Field(default=False, description="Tax included in subtotal")


class TaxCalculationResponse(BaseModel):
    """Response schema for tax calculation"""

    subtotal: float
    tax_amount: float
    total_amount: float
    tax_rate: Optional[float] = None
    tax_name: Optional[str] = None
    tax_rate_id: Optional[int] = None
    calculation_id: Optional[int] = None
    tax_exempt: bool = False
    currency: str = "USD"


class TaxCalculationDetail(BaseModel):
    """Detailed tax calculation record"""

    id: int
    user_id: int
    order_id: Optional[int]
    payment_id: Optional[int]
    subscription_id: Optional[int]

    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str

    billing_country: Optional[str]
    billing_state: Optional[str]

    tax_exempt: bool
    tax_exempt_reason: Optional[str]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Tax Exemption Schemas
class TaxExemptionBase(BaseModel):
    exemption_type: str = Field(
        ..., max_length=50, description="nonprofit, educational, government"
    )
    exemption_certificate: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)

    country_code: Optional[str] = Field(None, max_length=2)
    state_code: Optional[str] = Field(None, max_length=10)
    applies_to_all: bool = False

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    certificate_url: Optional[str] = None
    notes: Optional[str] = None


class TaxExemptionCreate(TaxExemptionBase):
    """Schema for creating a tax exemption"""

    user_id: int


class TaxExemptionResponse(TaxExemptionBase):
    """Schema for tax exemption response"""

    id: int
    user_id: int
    organization_id: Optional[int]
    is_active: bool
    verified: bool
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Tax Report Schemas
class TaxReportRequest(BaseModel):
    """Request schema for tax reports"""

    start_date: datetime
    end_date: datetime
    country_code: Optional[str] = None
    state_code: Optional[str] = None


class TaxReportResponse(BaseModel):
    """Response schema for tax reports"""

    start_date: datetime
    end_date: datetime
    total_transactions: int
    total_tax_collected: Decimal
    total_sales: Decimal
    currency: str = "USD"

    # Breakdown by region
    by_region: dict = {}

    # Breakdown by product type
    by_product_type: dict = {}
