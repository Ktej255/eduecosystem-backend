"""
Advanced Revenue Analytics Service
Revenue forecasting, trends, and comparative analysis
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics

from app.models.order import Order, OrderStatus, OrderItem
from app.models.course import Course


class RevenueAnalyticsService:
    """Advanced revenue analytics and forecasting"""

    def __init__(self, db: Session):
        self.db = db

    def forecast_revenue(
        self,
        instructor_id: Optional[int] = None,
        course_id: Optional[int] = None,
        forecast_days: int = 30,
    ) -> Dict:
        """
        Forecast future revenue based on historical trends.

        Uses simple linear regression on historical data.
        """
        # Get historical data (last 90 days)
        lookback_days = 90
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Query revenue data
        query = self.db.query(
            func.date(Order.created_at).label("date"),
            func.sum(Order.total).label("revenue"),
        ).filter(Order.status == OrderStatus.COMPLETED, Order.created_at >= start_date)

        if instructor_id:
            # Join with courses to filter by instructor
            query = (
                query.join(OrderItem)
                .join(Course)
                .filter(Course.instructor_id == instructor_id)
            )

        if course_id:
            query = query.join(OrderItem).filter(OrderItem.course_id == course_id)

        query = query.group_by(func.date(Order.created_at))
        historical_data = query.all()

        if len(historical_data) < 7:
            return {
                "forecast_period_days": forecast_days,
                "predicted_revenue": 0.0,
                "confidence_interval": [0.0, 0.0],
                "trend": "insufficient_data",
                "historical_average": 0.0,
                "message": "Not enough historical data for reliable forecast",
            }

        # Extract daily revenues
        daily_revenues = [float(row.revenue) for row in historical_data]

        # Calculate trend using simple moving average
        avg_daily_revenue = statistics.mean(daily_revenues)

        # Calculate trend (last 30 days vs previous 30 days)
        if len(daily_revenues) >= 60:
            recent_avg = statistics.mean(daily_revenues[-30:])
            previous_avg = statistics.mean(daily_revenues[-60:-30])
            growth_rate = (
                (recent_avg - previous_avg) / previous_avg if previous_avg > 0 else 0
            )
        else:
            recent_avg = avg_daily_revenue
            growth_rate = 0

        # Forecast using recent average + growth
        predicted_daily = recent_avg * (1 + growth_rate)
        predicted_revenue = predicted_daily * forecast_days

        # Calculate confidence interval (±20% based on std deviation)
        std_dev = statistics.stdev(daily_revenues) if len(daily_revenues) > 1 else 0
        confidence_range = std_dev * forecast_days

        lower_bound = max(0, predicted_revenue - confidence_range)
        upper_bound = predicted_revenue + confidence_range

        # Determine trend
        if growth_rate > 0.1:
            trend = "upward"
        elif growth_rate < -0.1:
            trend = "downward"
        else:
            trend = "stable"

        return {
            "forecast_period_days": forecast_days,
            "predicted_revenue": round(predicted_revenue, 2),
            "predicted_daily_avg": round(predicted_daily, 2),
            "confidence_interval": [round(lower_bound, 2), round(upper_bound, 2)],
            "trend": trend,
            "growth_rate": round(growth_rate * 100, 2),  # as percentage
            "historical_average": round(avg_daily_revenue, 2),
            "historical_days": len(daily_revenues),
            "breakdown_by_week": self._forecast_by_week(predicted_daily, forecast_days),
        }

    def _forecast_by_week(self, daily_avg: float, total_days: int) -> List[Dict]:
        """Break down forecast into weekly predictions"""
        weeks = []
        remaining_days = total_days
        week_num = 1

        while remaining_days > 0:
            days_in_week = min(7, remaining_days)
            weeks.append(
                {
                    "week": week_num,
                    "days": days_in_week,
                    "predicted_revenue": round(daily_avg * days_in_week, 2),
                }
            )
            remaining_days -= 7
            week_num += 1

        return weeks

    def get_revenue_breakdown(
        self,
        instructor_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """
        Get detailed revenue breakdown by various dimensions.
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()
        if not end_date:
            end_date = datetime.now().date()

        # Base query
        query = self.db.query(Order).filter(
            Order.status == OrderStatus.COMPLETED,
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date,
        )

        if instructor_id:
            from app.models.order import OrderItem

            query = (
                query.join(OrderItem)
                .join(Course)
                .filter(Course.instructor_id == instructor_id)
            )

        orders = query.all()

        total_revenue = sum(order.total for order in orders)

        # Breakdown by course
        course_revenue = {}
        for order in orders:
            for item in order.items:
                if item.course_id:
                    course_name = item.item_name
                    course_revenue[course_name] = (
                        course_revenue.get(course_name, 0) + item.total
                    )

        # Breakdown by payment method (if available in future)
        # For now, placeholder

        # Breakdown by day of week
        dow_revenue = {i: 0 for i in range(7)}  # 0=Monday, 6=Sunday
        for order in orders:
            dow = order.created_at.weekday()
            dow_revenue[dow] += order.total

        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        return {
            "period": {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "days": (end_date - start_date).days + 1,
            },
            "total_revenue": round(total_revenue, 2),
            "order_count": len(orders),
            "average_order_value": round(total_revenue / len(orders), 2)
            if orders
            else 0,
            "by_course": [
                {
                    "course": name,
                    "revenue": round(rev, 2),
                    "percentage": round(rev / total_revenue * 100, 2),
                }
                for name, rev in sorted(
                    course_revenue.items(), key=lambda x: x[1], reverse=True
                )
            ]
            if total_revenue > 0
            else [],
            "by_day_of_week": [
                {"day": day_names[i], "revenue": round(rev, 2)}
                for i, rev in dow_revenue.items()
            ],
        }

    def compare_periods(
        self,
        instructor_id: Optional[int] = None,
        course_id: Optional[int] = None,
        comparison_type: str = "mom",  # mom, yoy, custom
    ) -> Dict:
        """
        Compare revenue between two time periods.
        mom = month-over-month, yoy = year-over-year
        """
        end_date = datetime.now().date()

        if comparison_type == "mom":
            # Current month vs previous month
            current_start = end_date.replace(day=1)
            current_end = end_date

            # Previous month
            if current_start.month == 1:
                prev_start = current_start.replace(
                    year=current_start.year - 1, month=12, day=1
                )
            else:
                prev_start = current_start.replace(month=current_start.month - 1, day=1)

            # Last day of previous month
            prev_end = current_start - timedelta(days=1)

        elif comparison_type == "yoy":
            # Current year vs previous year (same period)
            current_start = end_date.replace(month=1, day=1)
            current_end = end_date
            prev_start = current_start.replace(year=current_start.year - 1)
            prev_end = end_date.replace(year=end_date.year - 1)

        else:
            # Default to last 30 days vs previous 30 days
            current_end = end_date
            current_start = end_date - timedelta(days=30)
            prev_end = current_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=30)

        # Get revenue for both periods
        current_revenue = self._get_period_revenue(
            current_start, current_end, instructor_id, course_id
        )
        previous_revenue = self._get_period_revenue(
            prev_start, prev_end, instructor_id, course_id
        )

        # Calculate change
        if previous_revenue > 0:
            change_amount = current_revenue - previous_revenue
            change_percent = (change_amount / previous_revenue) * 100
        else:
            change_amount = current_revenue
            change_percent = 100 if current_revenue > 0 else 0

        return {
            "comparison_type": comparison_type,
            "current_period": {
                "start": str(current_start),
                "end": str(current_end),
                "revenue": round(current_revenue, 2),
            },
            "previous_period": {
                "start": str(prev_start),
                "end": str(prev_end),
                "revenue": round(previous_revenue, 2),
            },
            "change": {
                "amount": round(change_amount, 2),
                "percentage": round(change_percent, 2),
                "trend": "up"
                if change_amount > 0
                else "down"
                if change_amount < 0
                else "flat",
            },
        }

    def _get_period_revenue(
        self,
        start_date: date,
        end_date: date,
        instructor_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> float:
        """Helper to get revenue for a specific period"""
        from app.models.order import OrderItem

        query = self.db.query(func.sum(Order.total)).filter(
            Order.status == OrderStatus.COMPLETED,
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date,
        )

        if instructor_id:
            query = (
                query.join(OrderItem)
                .join(Course)
                .filter(Course.instructor_id == instructor_id)
            )

        if course_id:
            query = query.join(OrderItem).filter(OrderItem.course_id == course_id)

        result = query.scalar()
        return float(result) if result else 0.0

    def calculate_ltv(
        self, instructor_id: Optional[int] = None, lookback_days: int = 365
    ) -> Dict:
        """
        Calculate Customer Lifetime Value metrics.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Get all completed orders in period
        query = self.db.query(Order).filter(
            Order.status == OrderStatus.COMPLETED,
            Order.created_at >= start_date,
            Order.user_id.isnot(None),  # Only registered users
        )

        if instructor_id:
            from app.models.order import OrderItem

            query = (
                query.join(OrderItem)
                .join(Course)
                .filter(Course.instructor_id == instructor_id)
            )

        orders = query.all()

        # Calculate per-customer metrics
        customer_data = {}
        for order in orders:
            user_id = order.user_id
            if user_id not in customer_data:
                customer_data[user_id] = {
                    "orders": 0,
                    "total_spent": 0,
                    "first_order": order.created_at,
                    "last_order": order.created_at,
                }

            customer_data[user_id]["orders"] += 1
            customer_data[user_id]["total_spent"] += order.total
            customer_data[user_id]["last_order"] = max(
                customer_data[user_id]["last_order"], order.created_at
            )

        if not customer_data:
            return {
                "total_customers": 0,
                "avg_ltv": 0,
                "avg_orders_per_customer": 0,
                "repeat_customer_rate": 0,
                "message": "No customer data available",
            }

        # Calculate metrics
        total_customers = len(customer_data)
        repeat_customers = len([c for c in customer_data.values() if c["orders"] > 1])

        avg_ltv = statistics.mean([c["total_spent"] for c in customer_data.values()])
        avg_orders = statistics.mean([c["orders"] for c in customer_data.values()])

        return {
            "period_days": lookback_days,
            "total_customers": total_customers,
            "repeat_customers": repeat_customers,
            "repeat_customer_rate": round(
                (repeat_customers / total_customers) * 100, 2
            ),
            "avg_ltv": round(avg_ltv, 2),
            "avg_orders_per_customer": round(avg_orders, 2),
            "top_customers": self._get_top_customers(customer_data, top_n=10),
        }

    def _get_top_customers(self, customer_data: Dict, top_n: int = 10) -> List[Dict]:
        """Get top customers by spending"""
        sorted_customers = sorted(
            customer_data.items(), key=lambda x: x[1]["total_spent"], reverse=True
        )[:top_n]

        return [
            {
                "user_id": user_id,
                "total_spent": round(data["total_spent"], 2),
                "order_count": data["orders"],
            }
            for user_id, data in sorted_customers
        ]
