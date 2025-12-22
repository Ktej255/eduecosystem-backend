"""
Tax Service

Service for calculating and managing taxes on transactions.
"""

from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.tax import TaxRate, TaxCalculation, TaxExemption


class TaxService:
    """Service for tax calculations and management"""

    @staticmethod
    def get_applicable_tax_rate(
        db: Session,
        country_code: str,
        state_code: Optional[str] = None,
        product_type: str = "digital_goods",
    ) -> Optional[TaxRate]:
        """
        Get applicable tax rate for a location and product type.

        Args:
            db: Database session
            country_code: ISO 3166-1 alpha-2 country code
            state_code: State/Province code
            product_type: Type of product (digital_goods, physical_goods, services, subscriptions)

        Returns:
            TaxRate object or None
        """
        query = db.query(TaxRate).filter(
            TaxRate.country_code == country_code.upper(), TaxRate.is_active == True
        )

        # Filter by state if provided
        if state_code:
            query = query.filter(TaxRate.state_code == state_code.upper())

        # Filter by product type applicability
        if product_type == "digital_goods":
            query = query.filter(TaxRate.applies_to_digital_goods == True)
        elif product_type == "physical_goods":
            query = query.filter(TaxRate.applies_to_physical_goods == True)
        elif product_type == "services":
            query = query.filter(TaxRate.applies_to_services == True)
        elif product_type == "subscriptions":
            query = query.filter(TaxRate.applies_to_subscriptions == True)

        # Check effective dates
        now = datetime.utcnow()
        query = query.filter(
            or_(TaxRate.effective_from == None, TaxRate.effective_from <= now),
            or_(TaxRate.effective_until == None, TaxRate.effective_until >= now),
        )

        # Order by specificity (state-level before country-level)
        if state_code:
            query = query.order_by(TaxRate.state_code.desc())

        return query.first()

    @staticmethod
    def calculate_tax(
        db: Session,
        user_id: int,
        subtotal: Decimal,
        country_code: str,
        state_code: Optional[str] = None,
        product_type: str = "digital_goods",
        is_inclusive: bool = False,
        order_id: Optional[int] = None,
        payment_id: Optional[int] = None,
        subscription_id: Optional[int] = None,
    ) -> Dict:
        """
        Calculate tax for a transaction.

        Args:
            db: Database session
            user_id: User making the purchase
            subtotal: Amount before tax
            country_code: Billing country
            state_code: Billing state
            product_type: Type of product
            is_inclusive: Whether tax is included in subtotal
            order_id: Related order ID
            payment_id: Related payment ID
            subscription_id: Related subscription ID

        Returns:
            Dict with tax_amount, total_amount, and tax_rate_id
        """
        # Check for tax exemption
        exemption = TaxService.check_tax_exemption(
            db, user_id, country_code, state_code
        )

        if exemption:
            return {
                "subtotal": float(subtotal),
                "tax_amount": 0.0,
                "total_amount": float(subtotal),
                "tax_rate_id": None,
                "tax_exempt": True,
                "currency": "USD",
            }

        # Get applicable tax rate
        tax_rate = TaxService.get_applicable_tax_rate(
            db, country_code, state_code, product_type
        )

        if not tax_rate:
            # No tax applicable
            return {
                "subtotal": float(subtotal),
                "tax_amount": 0.0,
                "total_amount": float(subtotal),
                "tax_rate_id": None,
                "tax_exempt": False,
                "currency": "USD",
            }

        # Calculate tax
        if is_inclusive:
            # Tax is included in the subtotal
            # subtotal = amount + (amount * rate)
            # amount = subtotal / (1 + rate)
            amount_before_tax = subtotal / (1 + tax_rate.tax_rate)
            tax_amount = subtotal - amount_before_tax
            total_amount = subtotal
        else:
            # Tax is added to subtotal
            tax_amount = subtotal * tax_rate.tax_rate
            total_amount = subtotal + tax_amount

        # Round to 2 decimal places
        tax_amount = Decimal(str(round(float(tax_amount), 2)))
        total_amount = Decimal(str(round(float(total_amount), 2)))

        # Create tax calculation record
        calculation = TaxCalculation(
            user_id=user_id,
            order_id=order_id,
            payment_id=payment_id,
            subscription_id=subscription_id,
            tax_rate_id=tax_rate.id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            billing_country=country_code,
            billing_state=state_code,
            is_inclusive=is_inclusive,
            tax_exempt=False,
        )

        db.add(calculation)
        db.commit()
        db.refresh(calculation)

        return {
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "tax_rate": float(tax_rate.tax_rate),
            "tax_name": tax_rate.tax_name,
            "tax_rate_id": tax_rate.id,
            "calculation_id": calculation.id,
            "tax_exempt": False,
            "currency": "USD",
        }

    @staticmethod
    def check_tax_exemption(
        db: Session,
        user_id: int,
        country_code: Optional[str] = None,
        state_code: Optional[str] = None,
    ) -> Optional[TaxExemption]:
        """
        Check if user has a valid tax exemption.

        Args:
            db: Database session
            user_id: User ID
            country_code: Country code to check
            state_code: State code to check

        Returns:
            TaxExemption object or None
        """
        query = db.query(TaxExemption).filter(
            TaxExemption.user_id == user_id,
            TaxExemption.is_active == True,
            TaxExemption.verified == True,
        )

        # Check validity dates
        now = datetime.utcnow()
        query = query.filter(
            or_(TaxExemption.valid_from == None, TaxExemption.valid_from <= now),
            or_(TaxExemption.valid_until == None, TaxExemption.valid_until >= now),
        )

        # Check location match or global exemption
        if country_code:
            query = query.filter(
                or_(TaxExemption.applies_to_all == True,
                    TaxExemption.country_code == country_code)
            )

        if state_code:
            query = query.filter(
                or_(TaxExemption.state_code == None,
                    TaxExemption.state_code == state_code)
            )

        return query.first()

    @staticmethod
    def create_tax_rate(
        db: Session,
        country_code: str,
        region_name: str,
        tax_name: str,
        tax_rate: Decimal,
        state_code: Optional[str] = None,
        **kwargs,
    ) -> TaxRate:
        """
        Create a new tax rate configuration.

        Args:
            db: Database session
            country_code: ISO country code
            region_name: Name of the region
            tax_name: Name of the tax (e.g., "VAT", "GST")
            tax_rate: Tax rate as decimal (e.g., 0.20 for 20%)
            state_code: Optional state code
            **kwargs: Additional tax rate fields

        Returns:
            Created TaxRate object
        """
        tax_rate_obj = TaxRate(
            country_code=country_code.upper(),
            state_code=state_code.upper() if state_code else None,
            region_name=region_name,
            tax_name=tax_name,
            tax_rate=tax_rate,
            **kwargs,
        )

        db.add(tax_rate_obj)
        db.commit()
        db.refresh(tax_rate_obj)

        return tax_rate_obj

    @staticmethod
    def get_tax_rates(
        db: Session, country_code: Optional[str] = None, active_only: bool = True
    ) -> List[TaxRate]:
        """
        Get all tax rates, optionally filtered by country.

        Args:
            db: Database session
            country_code: Optional country filter
            active_only: Only return active rates

        Returns:
            List of TaxRate objects
        """
        query = db.query(TaxRate)

        if country_code:
            query = query.filter(TaxRate.country_code == country_code.upper())

        if active_only:
            query = query.filter(TaxRate.is_active == True)

        return query.order_by(TaxRate.country_code, TaxRate.state_code).all()

    @staticmethod
    def update_tax_rate(db: Session, tax_rate_id: int, **updates) -> TaxRate:
        """
        Update a tax rate.

        Args:
            db: Database session
            tax_rate_id: Tax rate ID
            **updates: Fields to update

        Returns:
            Updated TaxRate object
        """
        tax_rate = db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()

        if not tax_rate:
            raise ValueError("Tax rate not found")

        for key, value in updates.items():
            if hasattr(tax_rate, key):
                setattr(tax_rate, key, value)

        db.commit()
        db.refresh(tax_rate)

        return tax_rate

    @staticmethod
    def delete_tax_rate(db: Session, tax_rate_id: int) -> bool:
        """
        Deactivate a tax rate (soft delete).

        Args:
            db: Database session
            tax_rate_id: Tax rate ID

        Returns:
            True if successful
        """
        tax_rate = db.query(TaxRate).filter(TaxRate.id == tax_rate_id).first()

        if not tax_rate:
            return False

        tax_rate.is_active = False
        db.commit()

        return True
