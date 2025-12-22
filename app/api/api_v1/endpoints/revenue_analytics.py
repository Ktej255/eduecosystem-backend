"""
Advanced Revenue Analytics API Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.api import deps
from app.models.user import User
from app.services.revenue_analytics_service import RevenueAnalyticsService

router = APIRouter()


@router.get("/revenue/forecast")
def get_revenue_forecast(
    forecast_days: int = Query(
        30, ge=7, le=365, description="Number of days to forecast"
    ),
    course_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Get revenue forecast for instructor's courses.
    Uses historical data to predict future revenue.
    """
    service = RevenueAnalyticsService(db)
    return service.forecast_revenue(
        instructor_id=current_user.id, course_id=course_id, forecast_days=forecast_days
    )


@router.get("/revenue/breakdown")
def get_revenue_breakdown(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Get detailed revenue breakdown by course, day of week, etc.
    """
    service = RevenueAnalyticsService(db)
    return service.get_revenue_breakdown(
        instructor_id=current_user.id, start_date=start_date, end_date=end_date
    )


@router.get("/revenue/comparison")
def compare_revenue_periods(
    comparison_type: str = Query("mom", pattern="^(mom|yoy|custom)$"),
    course_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Compare revenue between periods.
    - mom: Month-over-month
    - yoy: Year-over-year
    - custom: Last 30 days vs previous 30 days
    """
    service = RevenueAnalyticsService(db)
    return service.compare_periods(
        instructor_id=current_user.id,
        course_id=course_id,
        comparison_type=comparison_type,
    )


@router.get("/revenue/ltv")
def get_customer_ltv(
    lookback_days: int = Query(365, ge=30, le=730),
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Get Customer Lifetime Value metrics.
    Shows repeat customer rate, average LTV, top customers.
    """
    service = RevenueAnalyticsService(db)
    return service.calculate_ltv(
        instructor_id=current_user.id, lookback_days=lookback_days
    )


# Admin endpoints (platform-wide)


@router.get("/admin/revenue/forecast")
def get_platform_revenue_forecast(
    forecast_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Get platform-wide revenue forecast (admin only).
    """
    service = RevenueAnalyticsService(db)
    return service.forecast_revenue(
        instructor_id=None,  # Platform-wide
        forecast_days=forecast_days,
    )


@router.get("/admin/revenue/breakdown")
def get_platform_revenue_breakdown(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Get platform-wide revenue breakdown (admin only).
    """
    service = RevenueAnalyticsService(db)
    return service.get_revenue_breakdown(
        instructor_id=None,  # Platform-wide
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/admin/revenue/ltv")
def get_platform_ltv(
    lookback_days: int = Query(365, ge=30, le=730),
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Get platform-wide LTV metrics (admin only).
    """
    service = RevenueAnalyticsService(db)
    return service.calculate_ltv(
        instructor_id=None,  # Platform-wide
        lookback_days=lookback_days,
    )
