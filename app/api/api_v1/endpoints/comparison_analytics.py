"""
Comparison Analytics API Endpoints

Provides endpoints for comparing courses and instructors.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.services.comparison_service import ComparisonService
from app.models.user import User

router = APIRouter()


@router.get("/compare/courses")
def compare_courses(
    course_ids: str = Query(..., description="Comma-separated course IDs"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Compare multiple courses side-by-side.

    Returns comparison metrics, insights, and benchmarks.
    """
    # Parse course IDs
    try:
        course_id_list = [int(id.strip()) for id in course_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid course IDs format")

    # Parse dates if provided
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    try:
        comparison_data = ComparisonService.compare_courses(
            db, course_id_list, start_dt, end_dt
        )
        return comparison_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/compare/instructors")
def compare_instructors(
    instructor_ids: str = Query(..., description="Comma-separated instructor IDs"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Compare instructor performance metrics.

    Requires admin role.
    """
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Parse instructor IDs
    try:
        instructor_id_list = [int(id.strip()) for id in instructor_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid instructor IDs format")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    try:
        comparison_data = ComparisonService.compare_instructors(
            db, instructor_id_list, start_dt, end_dt
        )
        return comparison_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
