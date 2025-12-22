"""
Executive Analytics Service

Provides high-level KPIs, platform health scoring,
and risk indicators for executive dashboard.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.order import Order
from app.models.course import Course
from app.models.course_review import CourseReview as Review


class ExecutiveService:
    """Service for executive-level analytics and KPIs"""

    @staticmethod
    def get_kpis(db: Session) -> Dict[str, Any]:
        """
        Calculate key platform KPIs.

        Returns comprehensive KPI metrics for executive dashboard.
        """
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        print("DEBUG: Starting get_kpis")

        # Active users
        print("DEBUG: Querying daily_active")
        daily_active = (
            db.query(func.count(func.distinct(Enrollment.user_id)))
            .filter(Enrollment.enrolled_at >= today_start)
            .scalar()
            or 0
        )

        weekly_active = (
            db.query(func.count(func.distinct(Enrollment.user_id)))
            .filter(Enrollment.enrolled_at >= week_start)
            .scalar()
            or 0
        )

        monthly_active = (
            db.query(func.count(func.distinct(Enrollment.user_id)))
            .filter(Enrollment.enrolled_at >= month_start)
            .scalar()
            or 0
        )

        # Total users
        print("DEBUG: Querying total_users")
        total_users = db.query(func.count(User.id)).scalar() or 0

        # Revenue metrics
        print("DEBUG: Querying total_revenue")
        total_revenue = (
            db.query(func.sum(Order.total)).filter(Order.status == "completed").scalar()
            or 0
        )

        monthly_revenue = (
            db.query(func.sum(Order.total))
            .filter(Order.status == "completed", Order.created_at >= month_start)
            .scalar()
            or 0
        )

        # Previous month revenue for growth calculation
        prev_month_start = month_start - timedelta(days=30)
        prev_month_revenue = (
            db.query(func.sum(Order.total))
            .filter(
                Order.status == "completed",
                Order.created_at >= prev_month_start,
                Order.created_at < month_start,
            )
            .scalar()
            or 0
        )

        revenue_growth = (
            ((monthly_revenue - prev_month_revenue) / prev_month_revenue * 100)
            if prev_month_revenue > 0
            else 0
        )

        # Course metrics
        print("DEBUG: Querying total_courses")
        total_courses = (
            db.query(func.count(Course.id)).filter(Course.is_published == True).scalar()
            or 0
        )

        total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0

        completed_enrollments = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == "completed")
            .scalar()
            or 0
        )

        completion_rate = (
            (completed_enrollments / total_enrollments * 100)
            if total_enrollments > 0
            else 0
        )

        # Average rating
        avg_rating = db.query(func.avg(Review.rating)).scalar() or 0

        # Calculate CAC (Customer Acquisition Cost) - simplified
        # In real scenario, would factor in marketing spend
        total_orders = (
            db.query(func.count(Order.id)).filter(Order.status == "completed").scalar()
            or 0
        )

        # Simplified CAC calculation
        cac = 50.0  # Placeholder - would calculate from actual marketing data

        # Calculate churn rate
        churned_users = (
            db.query(func.count(User.id)).filter(User.is_active == False).scalar() or 0
        )

        churn_rate = (churned_users / total_users * 100) if total_users > 0 else 0

        print("DEBUG: Finished get_kpis")
        return {
            "active_users": {
                "daily": daily_active,
                "weekly": weekly_active,
                "monthly": monthly_active,
                "total": total_users,
            },
            "revenue": {
                "total": float(total_revenue),
                "monthly": float(monthly_revenue),
                "growth_rate": round(revenue_growth, 2),
                "arr": float(
                    monthly_revenue * 12
                ),  # Annual Recurring Revenue projection
            },
            "courses": {
                "total_published": total_courses,
                "total_enrollments": total_enrollments,
                "completion_rate": round(completion_rate, 2),
            },
            "satisfaction": {
                "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
                "nps_score": 75,  # Placeholder - would calculate from actual NPS surveys
            },
            "business_metrics": {
                "cac": cac,
                "churn_rate": round(churn_rate, 2),
                "total_orders": total_orders,
            },
        }

    @staticmethod
    def calculate_health_score(db: Session) -> Dict[str, Any]:
        """
        Calculate platform health score (0-100).

        Uses weighted average of key metrics.
        """
        kpis = ExecutiveService.get_kpis(db)

        # Component scores (0-100)
        components = {}

        # User growth (25% weight)
        # Score based on monthly active users growth
        mau = kpis["active_users"]["monthly"]
        total_users = kpis["active_users"]["total"]
        user_engagement = (mau / total_users * 100) if total_users > 0 else 0
        components["user_engagement"] = min(user_engagement, 100)

        # Revenue growth (25% weight)
        revenue_growth = kpis["revenue"]["growth_rate"]
        # Normalize: 0% growth = 50, 20%+ growth = 100
        components["revenue_health"] = min(max(50 + revenue_growth * 2.5, 0), 100)

        # Completion rate (20% weight)
        completion_rate = kpis["courses"]["completion_rate"]
        components["course_completion"] = completion_rate

        # Customer satisfaction (15% weight)
        avg_rating = kpis["satisfaction"]["average_rating"]
        # Convert 0-5 scale to 0-100
        components["customer_satisfaction"] = (avg_rating / 5.0) * 100

        # Churn rate (15% weight)
        # Inverse: lower churn = higher score
        churn_rate = kpis["business_metrics"]["churn_rate"]
        components["retention"] = max(100 - (churn_rate * 20), 0)

        # Calculate weighted score
        health_score = (
            components["user_engagement"] * 0.25
            + components["revenue_health"] * 0.25
            + components["course_completion"] * 0.20
            + components["customer_satisfaction"] * 0.15
            + components["retention"] * 0.15
        )

        # Determine trend
        trend = "stable"
        if revenue_growth > 5:
            trend = "improving"
        elif revenue_growth < -5:
            trend = "declining"

        return {
            "score": round(health_score, 1),
            "grade": ExecutiveService._score_to_grade(health_score),
            "trend": trend,
            "components": {k: round(v, 1) for k, v in components.items()},
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def identify_risks(db: Session) -> List[Dict[str, Any]]:
        """
        Identify platform risks and issues requiring attention.

        Returns list of risk indicators with severity levels.
        """
        risks = []
        kpis = ExecutiveService.get_kpis(db)

        # Check churn rate
        churn_rate = kpis["business_metrics"]["churn_rate"]
        if churn_rate > 5:
            risks.append(
                {
                    "type": "high_churn",
                    "severity": "high" if churn_rate > 10 else "medium",
                    "value": churn_rate,
                    "message": f"Churn rate is {churn_rate}%, exceeding healthy threshold of 5%",
                    "recommendation": "Investigate user feedback and improve retention strategies",
                }
            )

        # Check completion rate
        completion_rate = kpis["courses"]["completion_rate"]
        if completion_rate < 50:
            risks.append(
                {
                    "type": "low_completion",
                    "severity": "high" if completion_rate < 30 else "medium",
                    "value": completion_rate,
                    "message": f"Course completion rate is {completion_rate}%, below target of 70%",
                    "recommendation": "Review course content quality and student engagement strategies",
                }
            )

        # Check revenue growth
        revenue_growth = kpis["revenue"]["growth_rate"]
        if revenue_growth < 0:
            risks.append(
                {
                    "type": "revenue_decline",
                    "severity": "high" if revenue_growth < -10 else "medium",
                    "value": revenue_growth,
                    "message": f"Revenue growth is negative at {revenue_growth}%",
                    "recommendation": "Analyze market trends and adjust pricing/marketing strategy",
                }
            )

        # Check user engagement
        mau = kpis["active_users"]["monthly"]
        total_users = kpis["active_users"]["total"]
        engagement_rate = (mau / total_users * 100) if total_users > 0 else 0

        if engagement_rate < 30:
            risks.append(
                {
                    "type": "low_engagement",
                    "severity": "medium",
                    "value": engagement_rate,
                    "message": f"Only {engagement_rate}% of users are active monthly",
                    "recommendation": "Enhance user communication and course recommendations",
                }
            )

        return risks

    @staticmethod
    def get_growth_metrics(db: Session) -> Dict[str, Any]:
        """
        Calculate growth metrics over time.

        Returns growth trends for key metrics.
        """
        now = datetime.utcnow()

        # Calculate metrics for last 6 months
        monthly_data = []

        for i in range(6):
            month_start = datetime(now.year, now.month, 1) - timedelta(days=30 * i)
            if month_start.month == 1:
                prev_month_start = datetime(month_start.year - 1, 12, 1)
            else:
                prev_month_start = datetime(month_start.year, month_start.month - 1, 1)

            # Get metrics for this month
            enrollments = (
                db.query(func.count(Enrollment.id))
                .filter(
                    Enrollment.enrolled_at >= prev_month_start,
                    Enrollment.enrolled_at < month_start,
                )
                .scalar()
                or 0
            )

            revenue = (
                db.query(func.sum(Order.total))
                .filter(
                    Order.status == "completed",
                    Order.created_at >= prev_month_start,
                    Order.created_at < month_start,
                )
                .scalar()
                or 0
            )

            new_users = (
                db.query(func.count(User.id))
                .filter(
                    User.created_at >= prev_month_start, User.created_at < month_start
                )
                .scalar()
                or 0
            )

            monthly_data.append(
                {
                    "month": prev_month_start.strftime("%Y-%m"),
                    "enrollments": enrollments,
                    "revenue": float(revenue),
                    "new_users": new_users,
                }
            )

        # Reverse so oldest is first
        monthly_data.reverse()

        return {"monthly_trends": monthly_data, "period": "6_months"}

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
