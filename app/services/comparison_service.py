"""
Course Comparison Service

Provides functionality to compare multiple courses side-by-side,
calculate benchmarks, and generate insights.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.order import Order, OrderItem
from app.models.course_review import CourseReview as Review


class ComparisonService:
    """Service for comparing courses and generating insights"""

    @staticmethod
    def compare_courses(
        db: Session,
        course_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Compare multiple courses across key metrics.

        Args:
            db: Database session
            course_ids: List of course IDs to compare (2-10)
            start_date: Optional start date for comparison period
            end_date: Optional end date for comparison period

        Returns:
            Dictionary with comparison data and insights
        """
        if len(course_ids) < 2:
            raise ValueError("At least 2 courses required for comparison")
        if len(course_ids) > 10:
            raise ValueError("Maximum 10 courses can be compared at once")

        # Get courses
        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
        if len(courses) != len(course_ids):
            raise ValueError("One or more course IDs not found")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        comparison_data = []

        for course in courses:
            metrics = ComparisonService._calculate_course_metrics(
                db, course, start_date, end_date
            )
            comparison_data.append(
                {
                    "course_id": course.id,
                    "course_name": course.title,
                    "metrics": metrics,
                }
            )

        # Generate insights
        insights = ComparisonService._generate_insights(comparison_data)

        # Calculate benchmarks
        benchmarks = ComparisonService._calculate_benchmarks(comparison_data)

        return {
            "courses": comparison_data,
            "insights": insights,
            "benchmarks": benchmarks,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

    @staticmethod
    def _calculate_course_metrics(
        db: Session, course: Course, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate metrics for a single course"""

        # Total enrollments
        total_enrollments = (
            db.query(func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.enrolled_at >= start_date,
                Enrollment.enrolled_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Active enrollments (not completed or dropped)
        active_enrollments = (
            db.query(func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.status.in_(["active", "in_progress"]),
                Enrollment.enrolled_at >= start_date,
                Enrollment.enrolled_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Completed enrollments
        completed_enrollments = (
            db.query(func.count(Enrollment.id))
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.status == "completed",
                Enrollment.enrolled_at >= start_date,
                Enrollment.enrolled_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Completion rate
        completion_rate = (
            (completed_enrollments / total_enrollments * 100)
            if total_enrollments > 0
            else 0
        )

        # Average rating
        avg_rating = (
            db.query(func.avg(Review.rating))
            .filter(
                Review.course_id == course.id,
                Review.created_at >= start_date,
                Review.created_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Total reviews
        total_reviews = (
            db.query(func.count(Review.id))
            .filter(
                Review.course_id == course.id,
                Review.created_at >= start_date,
                Review.created_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Revenue (from orders)
        revenue = (
            db.query(func.sum(OrderItem.subtotal))
            .join(Order)
            .filter(
                OrderItem.course_id == course.id,
                Order.status == "completed",
                Order.created_at >= start_date,
                Order.created_at <= end_date,
            )
            .scalar()
            or 0
        )

        # Average engagement (simplified - could use actual tracking data)
        avg_engagement = (
            active_enrollments / total_enrollments * 100 if total_enrollments > 0 else 0
        )

        # Average time to completion (in days)
        avg_completion_time = (
            db.query(
                func.avg(
                    func.julianday(Enrollment.completed_at)
                    - func.julianday(Enrollment.enrolled_at)
                )
            )
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.status == "completed",
                Enrollment.enrolled_at >= start_date,
                Enrollment.enrolled_at <= end_date,
            )
            .scalar()
            or 0
        )

        return {
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "completion_rate": round(completion_rate, 2),
            "average_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "total_reviews": total_reviews,
            "revenue": float(revenue),
            "revenue_per_enrollment": float(revenue / total_enrollments)
            if total_enrollments > 0
            else 0,
            "engagement_rate": round(avg_engagement, 2),
            "avg_completion_time_days": round(float(avg_completion_time), 1)
            if avg_completion_time
            else 0,
        }

    @staticmethod
    def _generate_insights(comparison_data: List[Dict]) -> List[str]:
        """Generate insights from comparison data"""
        insights = []

        # Find best performing course by completion rate
        best_completion = max(
            comparison_data, key=lambda x: x["metrics"]["completion_rate"]
        )
        insights.append(
            f"{best_completion['course_name']} has the highest completion rate at "
            f"{best_completion['metrics']['completion_rate']}%"
        )

        # Find highest rated course
        best_rated = max(comparison_data, key=lambda x: x["metrics"]["average_rating"])
        if best_rated["metrics"]["total_reviews"] > 0:
            insights.append(
                f"{best_rated['course_name']} has the highest average rating at "
                f"{best_rated['metrics']['average_rating']}/5.0"
            )

        # Find highest revenue course
        best_revenue = max(comparison_data, key=lambda x: x["metrics"]["revenue"])
        insights.append(
            f"{best_revenue['course_name']} generated the most revenue at "
            f"${best_revenue['metrics']['revenue']:,.2f}"
        )

        # Find most enrolled course
        most_enrolled = max(
            comparison_data, key=lambda x: x["metrics"]["total_enrollments"]
        )
        insights.append(
            f"{most_enrolled['course_name']} has the most enrollments with "
            f"{most_enrolled['metrics']['total_enrollments']} students"
        )

        # Find fastest completion
        fastest = min(
            comparison_data,
            key=lambda x: x["metrics"]["avg_completion_time_days"]
            if x["metrics"]["avg_completion_time_days"] > 0
            else float("inf"),
        )
        if fastest["metrics"]["avg_completion_time_days"] > 0:
            insights.append(
                f"{fastest['course_name']} has the fastest average completion time at "
                f"{fastest['metrics']['avg_completion_time_days']} days"
            )

        return insights

    @staticmethod
    def _calculate_benchmarks(comparison_data: List[Dict]) -> Dict[str, Any]:
        """Calculate benchmark statistics across all courses"""

        all_metrics = [c["metrics"] for c in comparison_data]

        return {
            "avg_completion_rate": round(
                sum(m["completion_rate"] for m in all_metrics) / len(all_metrics), 2
            ),
            "avg_rating": round(
                sum(m["average_rating"] for m in all_metrics) / len(all_metrics), 2
            ),
            "total_revenue": sum(m["revenue"] for m in all_metrics),
            "total_enrollments": sum(m["total_enrollments"] for m in all_metrics),
            "avg_revenue_per_enrollment": round(
                sum(m["revenue_per_enrollment"] for m in all_metrics)
                / len(all_metrics),
                2,
            ),
        }

    @staticmethod
    def compare_instructors(
        db: Session,
        instructor_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Compare instructor performance metrics.

        Args:
            db: Database session
            instructor_ids: List of instructor IDs
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Comparison data and benchmarks
        """
        # Implementation similar to compare_courses but aggregating by instructor
        # This would aggregate all courses taught by each instructor

        # Placeholder for now
        return {"instructors": [], "benchmarks": {}, "insights": []}
