"""
Coupon Management API Endpoints
Create, validate, and track discount coupons
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app import schemas
from app.api import deps
from app.models.user import User
from app.models.coupon import Coupon, CouponUsage
from app.models.course import Course

router = APIRouter()


@router.post("/", response_model=schemas.Coupon)
def create_coupon(
    coupon_in: schemas.CouponCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new coupon (instructor only)
    """
    # Check if code already exists
    existing = db.query(Coupon).filter(Coupon.code == coupon_in.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    # Verify course ownership if course-specific
    if coupon_in.course_id:
        course = db.query(Course).filter(Course.id == coupon_in.course_id).first()
        if not course or course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized for this course"
            )

    coupon = Coupon(
        **coupon_in.dict(), code=coupon_in.code.upper(), instructor_id=current_user.id
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon


@router.get("/", response_model=List[schemas.Coupon])
def list_coupons(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List instructor's coupons
    """
    coupons = (
        db.query(Coupon)
        .filter(Coupon.instructor_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return coupons


@router.get("/{coupon_id}", response_model=schemas.Coupon)
def get_coupon(
    coupon_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coupon details
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if coupon.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return coupon


@router.put("/{coupon_id}", response_model=schemas.Coupon)
def update_coupon(
    coupon_id: int,
    coupon_update: schemas.CouponUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update coupon
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if coupon.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in coupon_update.dict(exclude_unset=True).items():
        setattr(coupon, field, value)

    db.commit()
    db.refresh(coupon)

    return coupon


@router.delete("/{coupon_id}")
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete coupon
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if coupon.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(coupon)
    db.commit()

    return {"message": "Coupon deleted successfully"}


@router.post("/validate", response_model=schemas.CouponValidationResponse)
def validate_coupon(
    validation: schemas.CouponValidationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Validate coupon and calculate discount
    """
    # Find coupon
    coupon = (
        db.query(Coupon)
        .filter(Coupon.code == validation.code.upper(), Coupon.is_active == True)
        .first()
    )

    if not coupon:
        return schemas.CouponValidationResponse(
            valid=False, message="Invalid coupon code"
        )

    # Check validity period
    now = datetime.utcnow()
    if coupon.valid_from and coupon.valid_from > now:
        return schemas.CouponValidationResponse(
            valid=False, message="Coupon not yet valid"
        )

    if coupon.valid_until and coupon.valid_until < now:
        return schemas.CouponValidationResponse(
            valid=False, message="Coupon has expired"
        )

    # Check usage limits
    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
        return schemas.CouponValidationResponse(
            valid=False, message="Coupon usage limit reached"
        )

    # Check per-user limit
    user_usage_count = (
        db.query(func.count(CouponUsage.id))
        .filter(
            CouponUsage.coupon_id == coupon.id, CouponUsage.user_id == current_user.id
        )
        .scalar()
    )

    if user_usage_count >= coupon.usage_per_user_limit:
        return schemas.CouponValidationResponse(
            valid=False, message="You've already used this coupon"
        )

    # Check course restrictions
    if coupon.course_id and coupon.course_id != validation.course_id:
        return schemas.CouponValidationResponse(
            valid=False, message="Coupon not valid for this course"
        )

    # Check minimum purchase amount
    if validation.original_price < coupon.min_purchase_amount:
        return schemas.CouponValidationResponse(
            valid=False,
            message=f"Minimum purchase amount is ₹{coupon.min_purchase_amount}",
        )

    # Calculate discount
    if coupon.discount_type == "percentage":
        discount_amount = validation.original_price * (coupon.discount_value / 100)
        if coupon.max_discount_amount:
            discount_amount = min(discount_amount, coupon.max_discount_amount)
    else:  # fixed
        discount_amount = coupon.discount_value

    # Ensure discount doesn't exceed price
    discount_amount = min(discount_amount, validation.original_price)
    final_price = max(0, validation.original_price - discount_amount)

    return schemas.CouponValidationResponse(
        valid=True,
        message="Coupon applied successfully",
        discount_amount=discount_amount,
        final_price=final_price,
        coupon=coupon,
    )


@router.get("/{coupon_id}/analytics", response_model=schemas.CouponUsageStats)
def get_coupon_analytics(
    coupon_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get coupon usage analytics
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if coupon.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get usage stats
    usages = db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon_id).all()

    total_uses = len(usages)
    total_discount_given = sum(u.discount_amount for u in usages)
    total_revenue = sum(u.final_price for u in usages)
    unique_users = len(set(u.user_id for u in usages))
    average_discount = total_discount_given / total_uses if total_uses > 0 else 0

    return schemas.CouponUsageStats(
        total_uses=total_uses,
        total_discount_given=total_discount_given,
        total_revenue=total_revenue,
        unique_users=unique_users,
        average_discount=average_discount,
    )


@router.post("/{coupon_id}/record-usage")
def record_coupon_usage(
    coupon_id: int,
    payment_id: int,
    original_price: float,
    discount_amount: float,
    final_price: float,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Record coupon usage (called after successful payment)
    """
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    # Record usage
    usage = CouponUsage(
        coupon_id=coupon_id,
        user_id=current_user.id,
        payment_id=payment_id,
        original_price=original_price,
        discount_amount=discount_amount,
        final_price=final_price,
    )

    db.add(usage)

    # Increment usage count
    coupon.usage_count += 1

    db.commit()

    return {"message": "Coupon usage recorded"}
