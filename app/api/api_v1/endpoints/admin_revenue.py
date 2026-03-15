from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, cast, Date
from typing import Any, List, Dict
from datetime import datetime, timedelta
from app.api import deps
from app.models.user import User
from app.models.course_payment import CoursePayment
from app.models.course import Course
from app.models.marketing_automation import MessageLog, MarketingWorkflow

router = APIRouter()

@router.get("/overview", response_model=Dict[str, Any])
def get_revenue_overview(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    TASK 1.2 — REVENUE INTELLIGENCE OVERVIEW
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def get_sum(start_date):
        return db.query(func.sum(CoursePayment.amount)).filter(
            CoursePayment.status == "succeeded",
            CoursePayment.succeeded_at >= start_date
        ).scalar() or 0.0

    # Subject breakdown
    subject_stats = db.query(
        Course.category.label('subject'),
        func.sum(CoursePayment.amount).label('revenue'),
        func.count(CoursePayment.id).label('units_sold')
    ).join(CoursePayment, Course.id == CoursePayment.course_id).filter(
        CoursePayment.status == "succeeded"
    ).group_by(Course.category).all()

    # Daily trend (30d)
    thirty_days_ago = today_start - timedelta(days=30)
    daily_trend = db.query(
        func.date(CoursePayment.succeeded_at).label('date'),
        func.sum(CoursePayment.amount).label('revenue'),
        func.count(CoursePayment.id).label('transactions')
    ).filter(
        CoursePayment.status == "succeeded",
        CoursePayment.succeeded_at >= thirty_days_ago
    ).group_by(func.date(CoursePayment.succeeded_at)).order_by(func.date(CoursePayment.succeeded_at)).all()

    total_transactions = db.query(func.count(CoursePayment.id)).filter(
        CoursePayment.status == "succeeded"
    ).scalar() or 0
    
    total_all_time = db.query(func.sum(CoursePayment.amount)).filter(
        CoursePayment.status == "succeeded"
    ).scalar() or 0.0

    return {
        "today": float(get_sum(today_start)),
        "this_week": float(get_sum(week_start)),
        "this_month": float(get_sum(month_start)),
        "total_all_time": float(total_all_time),
        "avg_order_value": float(total_all_time / total_transactions) if total_transactions > 0 else 0.0,
        "total_transactions": int(total_transactions),
        "subject_breakdown": [
            {"subject": s.subject or "General", "revenue": float(s.revenue), "units_sold": int(s.units_sold)} 
            for s in subject_stats
        ],
        "daily_trend_30d": [
            {"date": str(d.date), "revenue": float(d.revenue), "transactions": int(d.transactions)}
            for d in daily_trend
        ],
        "top_converting_source": "Direct" , # Placeholder for source attribution logic
        "refund_count_month": 0,
        "refund_amount_month": 0.0
    }

@router.get("/marketing-roi", response_model=Dict[str, Any])
def get_marketing_roi(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    TASK 1.2 — MARKETING ROI
    Attribution logic: Enrollment within 7 days of receiving a marketing message.
    """
    campaigns = db.query(MarketingWorkflow).all()
    results = []

    for campaign in campaigns:
        # Messages sent for this campaign
        msg_count = db.query(func.count(MessageLog.id)).filter(
            MessageLog.workflow_id == campaign.id
        ).scalar() or 0

        # Attribution: Payment within 7 days of message
        # We find payments where user received a message from this campaign in the previous 7 days
        attributed_data = db.query(
            func.count(func.distinct(CoursePayment.user_id)).label('enrollments'),
            func.sum(CoursePayment.amount).label('revenue')
        ).join(
            MessageLog, MessageLog.user_id == CoursePayment.user_id
        ).filter(
            MessageLog.workflow_id == campaign.id,
            CoursePayment.status == "succeeded",
            CoursePayment.succeeded_at >= MessageLog.created_at,
            CoursePayment.succeeded_at <= MessageLog.created_at + timedelta(days=7)
        ).first()

        enrollments = attributed_data.enrollments or 0
        revenue = float(attributed_data.revenue or 0.0)
        
        # Heuristic cost (e.g., 0.5 INR per message)
        cost = msg_count * 0.5 
        
        results.append({
            "campaign_name": campaign.name,
            "messages_sent": msg_count,
            "enrollments_attributed": enrollments,
            "revenue_attributed": revenue,
            "cost_per_enrollment": revenue / enrollments if enrollments > 0 else 0.0,
            "roi_percentage": (revenue / cost * 100) if cost > 0 else 0.0
        })

    return {"campaigns": results}
