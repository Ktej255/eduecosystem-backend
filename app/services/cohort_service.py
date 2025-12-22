"""
Cohort Analysis Service

Provides functionality to create and analyze user cohorts,
track retention, and identify performance patterns.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from enum import Enum

from app.models.enrollment import Enrollment
from app.models.order import Order


class CohortType(str, Enum):
    """Types of cohorts"""

    ENROLLMENT_MONTH = "enrollment_month"
    COURSE = "course"
    SUBSCRIPTION = "subscription"
    REGISTRATION = "registration_month"


class CohortService:
    """Service for cohort analysis and tracking"""

    @staticmethod
    def create_enrollment_cohorts(db: Session) -> List[Dict[str, Any]]:
        """
        Create cohorts based on enrollment month.

        Returns list of cohorts with member counts.
        """
        # Group users by their first enrollment month
        cohorts_data = (
            db.query(
                func.strftime("%Y-%m", Enrollment.enrolled_at).label("cohort_month"),
                func.count(func.distinct(Enrollment.user_id)).label("member_count"),
            )
            .group_by("cohort_month")
            .order_by("cohort_month")
            .all()
        )

        cohorts = []
        for cohort_month, member_count in cohorts_data:
            cohorts.append(
                {
                    "name": f"Cohort {cohort_month}",
                    "cohort_type": CohortType.ENROLLMENT_MONTH,
                    "period": cohort_month,
                    "member_count": member_count,
                }
            )

        return cohorts

    @staticmethod
    def analyze_cohort_retention(
        db: Session,
        cohort_period: str,  # e.g., "2025-01"
        cohort_type: CohortType = CohortType.ENROLLMENT_MONTH,
    ) -> Dict[str, Any]:
        """
        Analyze retention for a specific cohort over time.

        Args:
            db: Database session
            cohort_period: Period identifier (e.g., "2025-01")
            cohort_type: Type of cohort analysis

        Returns:
            Retention data by time period
        """
        # Get cohort start and end dates
        year, month = map(int, cohort_period.split("-"))
        cohort_start = datetime(year, month, 1)

        # Calculate next month for end date
        if month == 12:
            cohort_end = datetime(year + 1, 1, 1)
        else:
            cohort_end = datetime(year, month + 1, 1)

        # Get all users who enrolled in this period
        cohort_users = (
            db.query(Enrollment.user_id)
            .filter(
                Enrollment.enrolled_at >= cohort_start,
                Enrollment.enrolled_at < cohort_end,
            )
            .distinct()
            .all()
        )

        cohort_user_ids = [u[0] for u in cohort_users]
        initial_size = len(cohort_user_ids)

        if initial_size == 0:
            return {
                "cohort_period": cohort_period,
                "initial_size": 0,
                "retention_data": [],
            }

        # Calculate retention for each month after cohort formation
        retention_data = []
        current_date = datetime.utcnow()

        for months_after in range(0, 13):  # Up to 12 months
            # Calculate the period to check
            check_month = month + months_after
            check_year = year
            while check_month > 12:
                check_month -= 12
                check_year += 1

            check_start = datetime(check_year, check_month, 1)
            if check_month == 12:
                check_end = datetime(check_year + 1, 1, 1)
            else:
                check_end = datetime(check_year, check_month + 1, 1)

            # Don't project into the future
            if check_start > current_date:
                break

            # Count active users in this period
            active_count = (
                db.query(func.count(func.distinct(Enrollment.user_id)))
                .filter(
                    Enrollment.user_id.in_(cohort_user_ids),
                    Enrollment.enrolled_at >= check_start,
                    Enrollment.enrolled_at < check_end,
                )
                .scalar()
                or 0
            )

            retention_rate = (
                (active_count / initial_size * 100) if initial_size > 0 else 0
            )

            retention_data.append(
                {
                    "months_after_formation": months_after,
                    "period": f"{check_year}-{check_month:02d}",
                    "active_users": active_count,
                    "retention_rate": round(retention_rate, 2),
                }
            )

        return {
            "cohort_period": cohort_period,
            "cohort_type": cohort_type.value,
            "initial_size": initial_size,
            "retention_data": retention_data,
        }

    @staticmethod
    def get_cohort_performance(db: Session, cohort_period: str) -> Dict[str, Any]:
        """
        Get performance metrics for a cohort.

        Returns completion rates, revenue, engagement, etc.
        """
        year, month = map(int, cohort_period.split("-"))
        cohort_start = datetime(year, month, 1)

        if month == 12:
            cohort_end = datetime(year + 1, 1, 1)
        else:
            cohort_end = datetime(year, month + 1, 1)

        # Get cohort members
        cohort_enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.enrolled_at >= cohort_start,
                Enrollment.enrolled_at < cohort_end,
            )
            .all()
        )

        total_enrollments = len(cohort_enrollments)

        if total_enrollments == 0:
            return {
                "cohort_period": cohort_period,
                "total_enrollments": 0,
                "metrics": {},
            }

        # Calculate metrics
        completed = sum(1 for e in cohort_enrollments if e.status == "completed")
        active = sum(
            1 for e in cohort_enrollments if e.status in ["active", "in_progress"]
        )

        # Get revenue for cohort
        cohort_user_ids = list(set(e.user_id for e in cohort_enrollments))
        total_revenue = (
            db.query(func.sum(Order.total))
            .filter(
                Order.user_id.in_(cohort_user_ids),
                Order.status == "completed",
                Order.created_at >= cohort_start,
            )
            .scalar()
            or 0
        )

        # Calculate LTV (lifetime value per user)
        unique_users = len(set(e.user_id for e in cohort_enrollments))
        ltv = total_revenue / unique_users if unique_users > 0 else 0

        return {
            "cohort_period": cohort_period,
            "total_enrollments": total_enrollments,
            "unique_users": unique_users,
            "metrics": {
                "completion_rate": round(completed / total_enrollments * 100, 2),
                "active_rate": round(active / total_enrollments * 100, 2),
                "total_revenue": float(total_revenue),
                "revenue_per_user": round(total_revenue / unique_users, 2)
                if unique_users > 0
                else 0,
                "ltv": round(ltv, 2),
                "avg_enrollments_per_user": round(total_enrollments / unique_users, 2)
                if unique_users > 0
                else 0,
            },
        }

    @staticmethod
    def compare_cohorts(db: Session, cohort_periods: List[str]) -> Dict[str, Any]:
        """
        Compare multiple cohorts side-by-side.

        Args:
            db: Database session
            cohort_periods: List of cohort periods to compare

        Returns:
            Comparison data
        """
        comparison_data = []

        for period in cohort_periods:
            performance = CohortService.get_cohort_performance(db, period)
            retention = CohortService.analyze_cohort_retention(db, period)

            comparison_data.append(
                {
                    "cohort_period": period,
                    "performance": performance,
                    "retention_summary": {
                        "initial_size": retention["initial_size"],
                        "month_1_retention": next(
                            (
                                r["retention_rate"]
                                for r in retention["retention_data"]
                                if r["months_after_formation"] == 1
                            ),
                            0,
                        ),
                        "month_3_retention": next(
                            (
                                r["retention_rate"]
                                for r in retention["retention_data"]
                                if r["months_after_formation"] == 3
                            ),
                            0,
                        ),
                        "month_6_retention": next(
                            (
                                r["retention_rate"]
                                for r in retention["retention_data"]
                                if r["months_after_formation"] == 6
                            ),
                            0,
                        ),
                    },
                }
            )

        # Generate insights
        insights = CohortService._generate_cohort_insights(comparison_data)

        return {"cohorts": comparison_data, "insights": insights}

    @staticmethod
    def _generate_cohort_insights(comparison_data: List[Dict]) -> List[str]:
        """Generate insights from cohort comparison"""
        insights = []

        if not comparison_data:
            return insights

        # Find cohort with best retention
        best_retention = max(
            comparison_data, key=lambda x: x["retention_summary"]["month_3_retention"]
        )
        insights.append(
            f"Cohort {best_retention['cohort_period']} has the best 3-month retention at "
            f"{best_retention['retention_summary']['month_3_retention']}%"
        )

        # Find cohort with highest LTV
        best_ltv = max(
            comparison_data, key=lambda x: x["performance"]["metrics"].get("ltv", 0)
        )
        insights.append(
            f"Cohort {best_ltv['cohort_period']} has the highest LTV at "
            f"${best_ltv['performance']['metrics']['ltv']}"
        )

        # Find largest cohort
        largest = max(
            comparison_data, key=lambda x: x["retention_summary"]["initial_size"]
        )
        insights.append(
            f"Cohort {largest['cohort_period']} is the largest with "
            f"{largest['retention_summary']['initial_size']} members"
        )

        return insights
