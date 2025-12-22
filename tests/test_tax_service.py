"""
Tax Service Tests

Tests for tax calculation and rate management.
"""

from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.tax_service import TaxService
from app.models.user import User


def test_create_tax_rate(db: Session):
    """Test creating a tax rate"""
    rate = TaxService.create_tax_rate(
        db=db,
        country_code="US",
        region_name="United States",
        tax_name="VAT",
        tax_rate=Decimal("0.20"),
    )

    assert rate.id is not None
    assert rate.country_code == "US"
    assert rate.tax_rate == Decimal("0.20")
    assert rate.is_active is True


def test_calculate_tax_no_exemption(db: Session, normal_user: User):
    """Test tax calculation without exemption"""
    # Create tax rate
    TaxService.create_tax_rate(
        db=db,
        country_code="US",
        state_code="CA",
        region_name="California",
        tax_name="Sales Tax",
        tax_rate=Decimal("0.0825"),
    )

    # Calculate tax
    result = TaxService.calculate_tax(
        db=db,
        user_id=normal_user.id,
        subtotal=Decimal("100.00"),
        country_code="US",
        state_code="CA",
    )

    assert result["subtotal"] == 100.00
    assert result["tax_amount"] == 8.25
    assert result["total_amount"] == 108.25
    assert result["tax_exempt"] is False


def test_calculate_tax_inclusive(db: Session, normal_user: User):
    """Test tax calculation with tax-inclusive pricing"""
    TaxService.create_tax_rate(
        db=db,
        country_code="GB",
        region_name="United Kingdom",
        tax_name="VAT",
        tax_rate=Decimal("0.20"),
    )

    result = TaxService.calculate_tax(
        db=db,
        user_id=normal_user.id,
        subtotal=Decimal("120.00"),
        country_code="GB",
        is_inclusive=True,
    )

    # 120 = amount + (amount * 0.20)
    # amount = 100
    # tax = 20
    assert result["subtotal"] == 120.00
    assert result["tax_amount"] == 20.00
    assert result["total_amount"] == 120.00


def test_get_applicable_tax_rate(db: Session):
    """Test retrieving applicable tax rate"""
    # Create multiple rates
    TaxService.create_tax_rate(
        db=db,
        country_code="US",
        region_name="United States (Federal)",
        tax_name="Federal Tax",
        tax_rate=Decimal("0.05"),
    )

    TaxService.create_tax_rate(
        db=db,
        country_code="US",
        state_code="TX",
        region_name="Texas",
        tax_name="State Tax",
        tax_rate=Decimal("0.0625"),
    )

    # Should prefer state-level rate
    rate = TaxService.get_applicable_tax_rate(db=db, country_code="US", state_code="TX")

    assert rate is not None
    assert rate.state_code == "TX"
    assert rate.tax_rate == Decimal("0.0625")


def test_product_type_filtering(db: Session):
    """Test tax rate filtering by product type"""
    TaxService.create_tax_rate(
        db=db,
        country_code="US",
        region_name="Digital Only",
        tax_name="Digital Tax",
        tax_rate=Decimal("0.10"),
        applies_to_digital_goods=True,
        applies_to_physical_goods=False,
        applies_to_services=False,
        applies_to_subscriptions=False,
    )

    # Should find rate for digital goods
    rate_digital = TaxService.get_applicable_tax_rate(
        db=db, country_code="US", product_type="digital_goods"
    )
    assert rate_digital is not None

    # Should not find rate for physical goods
    rate_physical = TaxService.get_applicable_tax_rate(
        db=db, country_code="US", product_type="physical_goods"
    )
    assert rate_physical is None


def test_update_tax_rate(db: Session):
    """Test updating a tax rate"""
    rate = TaxService.create_tax_rate(
        db=db,
        country_code="FR",
        region_name="France",
        tax_name="TVA",
        tax_rate=Decimal("0.20"),
    )

    updated = TaxService.update_tax_rate(
        db=db, tax_rate_id=rate.id, tax_rate=Decimal("0.22")
    )

    assert updated.tax_rate == Decimal("0.22")


def test_delete_tax_rate(db: Session):
    """Test deactivating a tax rate"""
    rate = TaxService.create_tax_rate(
        db=db,
        country_code="DE",
        region_name="Germany",
        tax_name="MwSt",
        tax_rate=Decimal("0.19"),
    )

    success = TaxService.delete_tax_rate(db=db, tax_rate_id=rate.id)
    assert success is True

    # Verify it's deactivated
    db.refresh(rate)
    assert rate.is_active is False


def test_no_tax_for_region(db: Session, normal_user: User):
    """Test calculation when no tax rate exists"""
    result = TaxService.calculate_tax(
        db=db,
        user_id=normal_user.id,
        subtotal=Decimal("100.00"),
        country_code="XX",  # Non-existent country
    )

    assert result["tax_amount"] == 0.0
    assert result["total_amount"] == 100.0
    assert result["tax_rate_id"] is None
