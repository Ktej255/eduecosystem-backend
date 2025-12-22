"""
Executive Analytics API Endpoints

Provides high-level KPIs and platform health metrics for executives.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.services.executive_service import ExecutiveService
from app.models.user import User

router = APIRouter()


@router.get("/kpis")
def get_executive_kpis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get key platform KPIs for executive dashboard.

    Requires admin role.

    Returns:
        - Active users (daily, weekly, monthly)
        - Revenue metrics and growth
        - Course performance
        - Customer satisfaction
        - Business metrics (CAC, churn, etc.)
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        kpis = ExecutiveService.get_kpis(db)
        return kpis
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate KPIs: {str(e)}"
        )


@router.get("/health")
def get_platform_health(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Calculate platform health score (0-100).

    Requires admin role.

    Returns weighted score based on:
    - User engagement (25%)
    - Revenue health (25%)
    - Course completion (20%)
    - Customer satisfaction (15%)
    - Retention (15%)
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        health_data = ExecutiveService.calculate_health_score(db)
        return health_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate health score: {str(e)}"
        )


@router.get("/risks")
def get_platform_risks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Identify platform risks and issues.

    Requires admin role.

    Returns list of risk indicators with:
    - Type of risk
    - Severity level (low/medium/high)
    - Current value
    - Description
    - Recommendations
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        risks = ExecutiveService.identify_risks(db)
        return {
            "risks": risks,
            "total_count": len(risks),
            "critical_count": sum(1 for r in risks if r["severity"] == "high"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to identify risks: {str(e)}"
        )


@router.get("/growth")
def get_growth_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get growth metrics over time.

    Requires admin role.

    Returns 6-month trend data for:
    - Enrollments
    - Revenue
    - New users
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        growth_data = ExecutiveService.get_growth_metrics(db)
        return growth_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get growth metrics: {str(e)}"
        )
