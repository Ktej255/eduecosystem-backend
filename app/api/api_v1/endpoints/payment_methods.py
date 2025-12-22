"""
Payment Method API Endpoints

Manage saved payment methods for users.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodUpdate,
)

router = APIRouter()


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
def get_payment_methods(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get all saved payment methods for the current user.
    """
    methods = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == current_user.id, PaymentMethod.is_active == True
        )
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        .all()
    )

    return methods


@router.post("/payment-methods", response_model=PaymentMethodResponse)
def add_payment_method(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    method_data: PaymentMethodCreate,
):
    """
    Add a new payment method.

    The gateway_token should be obtained from the payment gateway's client-side SDK
    (e.g., Stripe token, PayPal billing agreement ID).
    """
    # If this is set as default, unset other defaults
    if method_data.is_default:
        db.query(PaymentMethod).filter(PaymentMethod.user_id == current_user.id).update(
            {"is_default": False}
        )

    # Create payment method
    payment_method = PaymentMethod(
        user_id=current_user.id,
        gateway=method_data.gateway,
        method_type=method_data.method_type,
        gateway_token=method_data.gateway_token,
        gateway_customer_id=method_data.gateway_customer_id,
        display_name=method_data.display_name,
        last_four=method_data.last_four,
        card_brand=method_data.card_brand,
        expiry_month=method_data.expiry_month,
        expiry_year=method_data.expiry_year,
        paypal_email=method_data.paypal_email,
        is_default=method_data.is_default or False,
    )

    db.add(payment_method)
    db.commit()
    db.refresh(payment_method)

    return payment_method


@router.put("/payment-methods/{method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    method_id: int,
    method_update: PaymentMethodUpdate,
):
    """
    Update a payment method (e.g., set as default).
    """
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == current_user.id)
        .first()
    )

    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    # If setting as default, unset other defaults
    if method_update.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id, PaymentMethod.id != method_id
        ).update({"is_default": False})

    # Update fields
    if method_update.display_name is not None:
        method.display_name = method_update.display_name
    if method_update.is_default is not None:
        method.is_default = method_update.is_default

    db.commit()
    db.refresh(method)

    return method


@router.delete("/payment-methods/{method_id}")
def delete_payment_method(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    method_id: int,
):
    """
    Delete (deactivate) a payment method.
    """
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == current_user.id)
        .first()
    )

    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    # Soft delete
    method.is_active = False

    # If this was the default, set another as default
    if method.is_default:
        other_method = (
            db.query(PaymentMethod)
            .filter(
                PaymentMethod.user_id == current_user.id,
                PaymentMethod.id != method_id,
                PaymentMethod.is_active == True,
            )
            .first()
        )

        if other_method:
            other_method.is_default = True

    db.commit()

    return {"status": "success", "message": "Payment method removed"}


@router.post("/payment-methods/{method_id}/set-default")
def set_default_payment_method(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    method_id: int,
):
    """
    Set a payment method as the default.
    """
    method = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.id == method_id,
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_active == True,
        )
        .first()
    )

    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    # Unset all other defaults
    db.query(PaymentMethod).filter(PaymentMethod.user_id == current_user.id).update(
        {"is_default": False}
    )

    # Set this as default
    method.is_default = True
    db.commit()

    return {"status": "success", "message": "Default payment method updated"}
