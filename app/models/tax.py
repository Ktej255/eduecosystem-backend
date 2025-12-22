"""
Tax Models

Database models for tax rates and calculations.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class TaxRate(Base):
    """Tax rate configuration for different regions"""

    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    state_code = Column(String(10), nullable=True, index=True)  # State/Province code
    region_name = Column(String(100), nullable=False)
    tax_name = Column(String(50), nullable=False)  # e.g., "VAT", "GST", "Sales Tax"
    tax_rate = Column(Numeric(5, 4), nullable=False)  # e.g., 0.0825 for 8.25%
    tax_type = Column(
        String(20), nullable=False, default="percentage"
    )  # percentage, fixed

    # Tax applicability
    applies_to_digital_goods = Column(Boolean, default=True)
    applies_to_physical_goods = Column(Boolean, default=True)
    applies_to_services = Column(Boolean, default=True)
    applies_to_subscriptions = Column(Boolean, default=True)

    # Compound tax (tax on tax)
    is_compound = Column(Boolean, default=False)
    compound_order = Column(Integer, default=0)  # Order for compound calculations

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_until = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    tax_id_required = Column(Boolean, default=False)  # Whether tax ID is required

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    calculations = relationship("TaxCalculation", back_populates="tax_rate")


class TaxCalculation(Base):
    """Tax calculation records for orders/payments"""

    __tablename__ = "tax_calculations"

    id = Column(Integer, primary_key=True, index=True)

    # Related entities
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    payment_id = Column(
        Integer, ForeignKey("course_payments.id"), nullable=True, index=True
    )
    subscription_id = Column(
        Integer, ForeignKey("user_subscriptions.id"), nullable=True, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Tax details
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id"), nullable=False)

    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)  # Amount before tax
    tax_amount = Column(Numeric(10, 2), nullable=False)  # Calculated tax
    total_amount = Column(Numeric(10, 2), nullable=False)  # Amount after tax
    currency = Column(String(3), default="USD", nullable=False)

    # Location
    billing_country = Column(String(2), nullable=True)
    billing_state = Column(String(10), nullable=True)
    billing_zip = Column(String(20), nullable=True)

    # Customer tax info
    tax_id = Column(String(50), nullable=True)  # VAT/GST number if applicable
    tax_exempt = Column(Boolean, default=False)
    tax_exempt_reason = Column(String(200), nullable=True)

    # Calculation details
    calculation_method = Column(String(50), default="automatic")
    is_inclusive = Column(Boolean, default=False)  # Tax included in price

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tax_rate = relationship("TaxRate", back_populates="calculations")
    user = relationship("User")


class TaxExemption(Base):
    """Tax exemptions for users or organizations"""

    __tablename__ = "tax_exemptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )

    # Exemption details
    exemption_type = Column(
        String(50), nullable=False
    )  # nonprofit, educational, government
    exemption_certificate = Column(String(100), nullable=True)  # Certificate number
    tax_id = Column(String(50), nullable=True)  # Tax ID or VAT number

    # Scope
    country_code = Column(String(2), nullable=True)
    state_code = Column(String(10), nullable=True)
    applies_to_all = Column(Boolean, default=False)  # Applies to all taxes

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # Documents
    certificate_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
