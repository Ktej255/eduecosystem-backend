"""
Instructor Earnings & Sales Analytics Endpoints
Provides detailed revenue, sales, and transaction data for instructors
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.api import deps
from app.models.course_payment import CoursePayment
from app.models.course import Course
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class EarningsSummary(BaseModel):
    total_earnings: float
    monthly_earnings: float
    total_sales: int
    monthly_sales: int
    top_earning_course_id: Optional[int] = None
    top_earning_course_title: Optional[str] = None


class CourseSales(BaseModel):
    course_id: int
    course_title: str
    total_sales: int
    total_revenue: float
    average_price: float
    last_sale_date: Optional[datetime] = None


class Transaction(BaseModel):
    id: int
    course_id: int
    course_title: str
    student_name: str
    student_email: str
    amount: float
    currency: str
    status: str
    payment_provider: str
    created_at: datetime
    succeeded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MonthlyRevenue(BaseModel):
    month: str  # YYYY-MM format
    revenue: float
    sales_count: int


# ============================================================================
# EARNINGS ENDPOINTS
# ============================================================================


@router.get("/instructor/earnings/summary", response_model=EarningsSummary)
def get_earnings_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get instructor earnings summary with total and monthly breakdowns.
    """
    # Get instructor's courses
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return EarningsSummary(
            total_earnings=0, monthly_earnings=0, total_sales=0, monthly_sales=0
        )

    # Total earnings (succeeded payments only)
    total_earnings = (
        db.query(func.sum(CoursePayment.amount))
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "succeeded"
        )
        .scalar()
        or 0.0
    )

    # Total sales count
    total_sales = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "succeeded"
        )
        .count()
    )

    # Monthly stats (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    monthly_earnings = (
        db.query(func.sum(CoursePayment.amount))
        .filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "succeeded",
            CoursePayment.succeeded_at >= thirty_days_ago,
        )
        .scalar()
        or 0.0
    )

    monthly_sales = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "succeeded",
            CoursePayment.succeeded_at >= thirty_days_ago,
        )
        .count()
    )

    # Top earning course
    top_course = (
        db.query(CoursePayment.course_id, func.sum(CoursePayment.amount).label("total"))
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "succeeded"
        )
        .group_by(CoursePayment.course_id)
        .order_by(desc("total"))
        .first()
    )

    top_course_title = None
    top_course_id = None
    if top_course:
        top_course_id = top_course.course_id
        course = db.query(Course).filter(Course.id == top_course_id).first()
        if course:
            top_course_title = course.title

    return EarningsSummary(
        total_earnings=total_earnings,
        monthly_earnings=monthly_earnings,
        total_sales=total_sales,
        monthly_sales=monthly_sales,
        top_earning_course_id=top_course_id,
        top_earning_course_title=top_course_title,
    )


@router.get("/instructor/earnings/by-course", response_model=List[CourseSales])
def get_earnings_by_course(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get revenue breakdown by course.
    """
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return []

    # Get sales stats for each course
    course_stats = (
        db.query(
            CoursePayment.course_id,
            func.count(CoursePayment.id).label("sales_count"),
            func.sum(CoursePayment.amount).label("total_revenue"),
            func.avg(CoursePayment.amount).label("avg_price"),
            func.max(CoursePayment.succeeded_at).label("last_sale"),
        )
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "succeeded"
        )
        .group_by(CoursePayment.course_id)
        .all()
    )

    # Build response
    result = []
    for stat in course_stats:
        course = db.query(Course).filter(Course.id == stat.course_id).first()
        if course:
            result.append(
                CourseSales(
                    course_id=stat.course_id,
                    course_title=course.title,
                    total_sales=stat.sales_count,
                    total_revenue=stat.total_revenue or 0.0,
                    average_price=stat.avg_price or 0.0,
                    last_sale_date=stat.last_sale,
                )
            )

    # Sort by revenue descending
    result.sort(key=lambda x: x.total_revenue, reverse=True)
    return result


@router.get("/instructor/earnings/monthly", response_model=List[MonthlyRevenue])
def get_monthly_revenue(
    months: int = Query(default=12, le=24),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get monthly revenue breakdown for charts.
    """
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return []

    start_date = datetime.utcnow() - timedelta(days=months * 30)

    # Group by year-month
    monthly_data = (
        db.query(
            func.to_char(CoursePayment.succeeded_at, "YYYY-MM").label("month"),
            func.sum(CoursePayment.amount).label("revenue"),
            func.count(CoursePayment.id).label("sales_count"),
        )
        .filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "succeeded",
            CoursePayment.succeeded_at >= start_date,
        )
        .group_by(func.to_char(CoursePayment.succeeded_at, "YYYY-MM"))
        .order_by(func.to_char(CoursePayment.succeeded_at, "YYYY-MM"))
        .all()
    )

    result = []
    for data in monthly_data:
        result.append(
            MonthlyRevenue(
                month=data.month,
                revenue=data.revenue or 0.0,
                sales_count=data.sales_count,
            )
        )

    return result


@router.get("/instructor/transactions", response_model=List[Transaction])
def get_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    course_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed transaction history with filtering.
    """
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return []

    query = db.query(CoursePayment).filter(CoursePayment.course_id.in_(course_ids))

    # Apply filters
    if course_id:
        query = query.filter(CoursePayment.course_id == course_id)
    if status:
        query = query.filter(CoursePayment.status == status)

    # Order by most recent
    query = query.order_by(desc(CoursePayment.created_at))

    # Pagination
    payments = query.offset(skip).limit(limit).all()

    # Build response with course and user details
    result = []
    for payment in payments:
        course = db.query(Course).filter(Course.id == payment.course_id).first()
        user = db.query(User).filter(User.id == payment.user_id).first()

        if course and user:
            result.append(
                Transaction(
                    id=payment.id,
                    course_id=payment.course_id,
                    course_title=course.title,
                    student_name=user.full_name or user.email.split("@")[0],
                    student_email=user.email,
                    amount=payment.amount,
                    currency=payment.currency,
                    status=payment.status,
                    payment_provider=payment.payment_provider,
                    created_at=payment.created_at,
                    succeeded_at=payment.succeeded_at,
                )
            )

    return result


@router.get("/instructor/transactions/export")
def export_transactions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Export all transactions as CSV data.
    Returns CSV-formatted string.
    """
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        return {"csv": "No transactions found"}

    payments = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.course_id.in_(course_ids), CoursePayment.status == "succeeded"
        )
        .order_by(desc(CoursePayment.succeeded_at))
        .all()
    )

    # Build CSV
    csv_lines = ["Date,Course,Student,Amount,Currency,Payment Provider"]

    for payment in payments:
        course = db.query(Course).filter(Course.id == payment.course_id).first()
        user = db.query(User).filter(User.id == payment.user_id).first()

        if course and user:
            date_str = (
                payment.succeeded_at.strftime("%Y-%m-%d %H:%M")
                if payment.succeeded_at
                else ""
            )
            csv_lines.append(
                f"{date_str},{course.title},{user.email},{payment.amount},{payment.currency},{payment.payment_provider}"
            )

    return {"csv": "\n".join(csv_lines)}
