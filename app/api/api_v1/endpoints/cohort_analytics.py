"""
Cohort Analytics API Endpoints

Provides endpoints for cohort analysis and tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.services.cohort_service import CohortService, CohortType
from app.models.user import User

router = APIRouter()


@router.get("/cohorts")
def list_cohorts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    List all available cohorts.

    Requires admin/instructor role.
    """
    if current_user.role not in ["admin", "super_admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        cohorts = CohortService.create_enrollment_cohorts(db)
        return {"cohorts": cohorts, "total_count": len(cohorts)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch cohorts: {str(e)}"
        )


@router.get("/cohorts/{cohort_period}/retention")
def get_cohort_retention(
    cohort_period: str,
    cohort_type: CohortType = Query(CohortType.ENROLLMENT_MONTH),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get retention data for a specific cohort.

    Args:
        cohort_period: Period identifier (e.g., "2025-01")
        cohort_type: Type of cohort analysis
    """
    if current_user.role not in ["admin", "super_admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        retention_data = CohortService.analyze_cohort_retention(
            db, cohort_period, cohort_type
        )
        return retention_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze retention: {str(e)}"
        )


@router.get("/cohorts/{cohort_period}/performance")
def get_cohort_performance(
    cohort_period: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get performance metrics for a cohort.

    Returns completion rates, revenue, engagement, etc.
    """
    if current_user.role not in ["admin", "super_admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        performance_data = CohortService.get_cohort_performance(db, cohort_period)
        return performance_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance: {str(e)}"
        )


@router.get("/cohorts/compare")
def compare_cohorts(
    cohort_periods: str = Query(..., description="Comma-separated cohort periods"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Compare multiple cohorts side-by-side.

    Args:
        cohort_periods: Comma-separated periods (e.g., "2025-01,2025-02,2025-03")
    """
    if current_user.role not in ["admin", "super_admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Parse cohort periods
    try:
        period_list = [p.strip() for p in cohort_periods.split(",")]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cohort_periods format")

    try:
        comparison_data = CohortService.compare_cohorts(db, period_list)
        return comparison_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
