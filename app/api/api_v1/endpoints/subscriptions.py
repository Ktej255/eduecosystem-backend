"""
Subscription API Endpoints

Endpoints for managing subscription plans and user subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.schemas.marketplace import (
    PlanCreate, PlanResponse, SubscriptionResponse
)

router = APIRouter()

@router.get("/plans", response_model=List[PlanResponse])
def get_plans(
    db: Session = Depends(deps.get_db)
):
    """
    Get all active subscription plans.
    """
    return SubscriptionService.get_active_plans(db)

@router.post("/plans", response_model=PlanResponse)
def create_plan(
    plan_in: PlanCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Create a new subscription plan (Admin only).
    """
    try:
        return SubscriptionService.create_plan(
            db=db,
            name=plan_in.name,
            monthly_price=plan_in.monthly_price,
            yearly_price=plan_in.yearly_price,
            description=plan_in.description,
            features=plan_in.features,
            access_level=plan_in.access_level,
            trial_days=plan_in.trial_days
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=Optional[SubscriptionResponse])
def get_my_subscription(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get current user's active subscription.
    """
    return SubscriptionService.get_user_subscription(db, current_user.id)

@router.post("/subscribe")
async def subscribe(
    plan_id: int,
    billing_cycle: str = "monthly",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Subscribe to a plan.
    """
    try:
        sub = await SubscriptionService.subscribe_user(
            db=db,
            user_id=current_user.id,
            plan_id=plan_id,
            billing_cycle=billing_cycle
        )
        return sub
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel")
def cancel_subscription(
    immediate: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Cancel current subscription.
    """
    sub = SubscriptionService.get_user_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return SubscriptionService.cancel_subscription(db, sub.id, immediate)
