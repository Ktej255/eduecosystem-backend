"""
Tax API Endpoints

API endpoints for tax management and calculations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.tax_service import TaxService
from app.schemas.tax import (
    TaxRateCreate,
    TaxRateUpdate,
    TaxRateResponse,
    TaxCalculationRequest,
    TaxCalculationResponse,
    TaxCalculationDetail,
)

router = APIRouter()


@router.post("/calculate", response_model=TaxCalculationResponse)
def calculate_tax(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: TaxCalculationRequest,
):
    """
    Calculate tax for a transaction.

    - **subtotal**: Amount before tax
    - **country_code**: Billing country (ISO 3166-1 alpha-2)
    - **state_code**: Billing state/province code (optional)
    - **product_type**: Type of product (digital_goods, physical_goods, services, subscriptions)
    - **is_inclusive**: Whether tax is included in the subtotal
    """
    try:
        result = TaxService.calculate_tax(
            db=db,
            user_id=current_user.id,
            subtotal=request.subtotal,
            country_code=request.country_code,
            state_code=request.state_code,
            product_type=request.product_type,
            is_inclusive=request.is_inclusive,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rates", response_model=List[TaxRateResponse])
def get_tax_rates(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    country_code: Optional[str] = Query(None, max_length=2),
    active_only: bool = Query(True),
):
    """
    Get all tax rates (admin only).

    - **country_code**: Filter by country (optional)
    - **active_only**: Only return active rates
    """
    rates = TaxService.get_tax_rates(
        db=db, country_code=country_code, active_only=active_only
    )
    return rates


@router.post("/rates", response_model=TaxRateResponse)
def create_tax_rate(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    rate_in: TaxRateCreate,
):
    """
    Create a new tax rate (admin only).
    """
    try:
        rate = TaxService.create_tax_rate(
            db=db,
            country_code=rate_in.country_code,
            region_name=rate_in.region_name,
            tax_name=rate_in.tax_name,
            tax_rate=rate_in.tax_rate,
            state_code=rate_in.state_code,
            tax_type=rate_in.tax_type,
            applies_to_digital_goods=rate_in.applies_to_digital_goods,
            applies_to_physical_goods=rate_in.applies_to_physical_goods,
            applies_to_services=rate_in.applies_to_services,
            applies_to_subscriptions=rate_in.applies_to_subscriptions,
            is_compound=rate_in.is_compound,
            compound_order=rate_in.compound_order,
            description=rate_in.description,
            tax_id_required=rate_in.tax_id_required,
            effective_from=rate_in.effective_from,
            effective_until=rate_in.effective_until,
        )
        return rate
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/rates/{rate_id}", response_model=TaxRateResponse)
def update_tax_rate(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    rate_id: int,
    rate_update: TaxRateUpdate,
):
    """
    Update a tax rate (admin only).
    """
    try:
        updates = rate_update.dict(exclude_unset=True)
        rate = TaxService.update_tax_rate(db=db, tax_rate_id=rate_id, **updates)
        return rate
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rates/{rate_id}")
def delete_tax_rate(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    rate_id: int,
):
    """
    Deactivate a tax rate (admin only).
    """
    success = TaxService.delete_tax_rate(db=db, tax_rate_id=rate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return {"status": "success", "message": "Tax rate deactivated"}


@router.get("/rate/{country_code}", response_model=Optional[TaxRateResponse])
def get_applicable_rate(
    *,
    db: Session = Depends(deps.get_db),
    country_code: str,
    state_code: Optional[str] = Query(None),
    product_type: str = Query("digital_goods"),
):
    """
    Get applicable tax rate for a location and product type.

    - **country_code**: ISO 3166-1 alpha-2 country code
    - **state_code**: State/province code (optional)
    - **product_type**: digital_goods, physical_goods, services, subscriptions
    """
    rate = TaxService.get_applicable_tax_rate(
        db=db,
        country_code=country_code,
        state_code=state_code,
        product_type=product_type,
    )
    return rate


@router.get("/calculations", response_model=List[TaxCalculationDetail])
def get_tax_calculations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
):
    """
    Get user's tax calculation history.
    """
    from app.models.tax import TaxCalculation

    calculations = (
        db.query(TaxCalculation)
        .filter(TaxCalculation.user_id == current_user.id)
        .order_by(TaxCalculation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return calculations
