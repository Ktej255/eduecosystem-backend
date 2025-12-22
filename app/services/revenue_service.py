"""
Revenue Sharing Service

Business logic for revenue calculation, tracking, and distribution
between platform and instructors.
"""

from sqlalchemy.orm import Session
from app.models.marketplace import RevenueShare, RevenueTransaction, InstructorPayout
from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RevenueShareService:
    """Service for managing revenue sharing and instructor earnings."""

    @staticmethod
    def initialize_revenue_share(
        db: Session,
        course_id: int,
        instructor_id: int,
        platform_fee_percentage: Decimal = Decimal("30.00"),
    ) -> RevenueShare:
        """
        Initialize revenue sharing for a course.

        Args:
            db: Database session
            course_id: Course ID
            instructor_id: Instructor user ID
            platform_fee_percentage: Platform fee (default 30%)

        Returns:
            RevenueShare instance
        """
        # Check if already exists
        existing = (
            db.query(RevenueShare).filter(RevenueShare.course_id == course_id).first()
        )

        if existing:
            return existing

        instructor_percentage = Decimal("100.00") - platform_fee_percentage

        revenue_share = RevenueShare(
            course_id=course_id,
            instructor_id=instructor_id,
            platform_fee_percentage=platform_fee_percentage,
            instructor_percentage=instructor_percentage,
        )

        db.add(revenue_share)
        db.commit()
        db.refresh(revenue_share)

        logger.info(
            f"Initialized revenue share for course {course_id}: {platform_fee_percentage}% platform, {instructor_percentage}% instructor"
        )

        return revenue_share

    @staticmethod
    def record_sale(
        db: Session,
        course_id: int,
        instructor_id: int,
        student_id: int,
        amount: Decimal,
        payment_id: str,
        coupon_code: Optional[str] = None,
        discount_amount: Decimal = Decimal("0.00"),
        affiliate_id: Optional[int] = None,
        affiliate_commission_percentage: Decimal = Decimal("10.00"),
    ) -> RevenueTransaction:
        """
        Record a course sale and calculate revenue split.

        Args:
            db: Database session
            course_id: Course ID
            instructor_id: Instructor ID
            student_id: Student ID
            amount: Total sale amount
            payment_id: Payment transaction ID
            coupon_code: Applied coupon code
            discount_amount: Discount applied
            affiliate_id: Affiliate who referred (if any)
            affiliate_commission_percentage: Affiliate commission rate

        Returns:
            RevenueTransaction instance
        """
        # Get revenue share configuration
        revenue_share = (
            db.query(RevenueShare).filter(RevenueShare.course_id == course_id).first()
        )

        if not revenue_share:
            # Initialize with default split
            revenue_share = RevenueShareService.initialize_revenue_share(
                db, course_id, instructor_id
            )

        # Calculate splits
        platform_fee = amount * (revenue_share.platform_fee_percentage / Decimal("100"))
        instructor_earnings = amount * (
            revenue_share.instructor_percentage / Decimal("100")
        )

        # Calculate affiliate commission if applicable
        affiliate_commission = Decimal("0.00")
        if affiliate_id:
            affiliate_commission = amount * (
                affiliate_commission_percentage / Decimal("100")
            )
            # Deduct affiliate commission from platform fee
            platform_fee -= affiliate_commission

        # Create transaction record
        transaction = RevenueTransaction(
            course_id=course_id,
            instructor_id=instructor_id,
            student_id=student_id,
            transaction_type="course",
            total_amount=amount,
            platform_fee=platform_fee,
            instructor_earnings=instructor_earnings,
            payment_id=payment_id,
            coupon_code=coupon_code,
            discount_amount=discount_amount,
            affiliate_id=affiliate_id,
            affiliate_commission=affiliate_commission,
        )

        db.add(transaction)

        # Update revenue share totals
        revenue_share.total_revenue += amount
        revenue_share.platform_earnings += platform_fee
        revenue_share.instructor_earnings += instructor_earnings
        revenue_share.pending_payout += instructor_earnings
        revenue_share.total_enrollments += 1
        revenue_share.last_sale_date = datetime.utcnow()

        db.commit()
        db.refresh(transaction)

        logger.info(
            f"Recorded sale for course {course_id}: ${amount} (Instructor: ${instructor_earnings}, Platform: ${platform_fee}, Affiliate: ${affiliate_commission})"
        )

        return transaction

    @staticmethod
    def get_instructor_earnings(
        db: Session, instructor_id: int, include_pending: bool = True
    ) -> Dict[str, Decimal]:
        """
        Get instructor earnings summary.

        Args:
            db: Database session
            instructor_id: Instructor ID
            include_pending: Include pending payout amount

        Returns:
            Dictionary with earnings breakdown
        """
        revenue_shares = (
            db.query(RevenueShare)
            .filter(RevenueShare.instructor_id == instructor_id)
            .all()
        )

        total_revenue = Decimal("0.00")
        total_earnings = Decimal("0.00")
        pending_payout = Decimal("0.00")

        for share in revenue_shares:
            total_revenue += share.total_revenue
            total_earnings += share.instructor_earnings
            if include_pending:
                pending_payout += share.pending_payout

        # Get total paid out
        total_paid = db.query(InstructorPayout).filter(
            InstructorPayout.instructor_id == instructor_id,
            InstructorPayout.status == "completed",
        ).with_entities(func.sum(InstructorPayout.amount)).scalar() or Decimal("0.00")

        return {
            "total_revenue": total_revenue,
            "total_earnings": total_earnings,
            "pending_payout": pending_payout,
            "total_paid": total_paid,
            "available_balance": pending_payout,
        }

    @staticmethod
    def get_course_revenue_breakdown(db: Session, course_id: int) -> Dict[str, any]:
        """
        Get detailed revenue breakdown for a course.

        Args:
            db: Database session
            course_id: Course ID

        Returns:
            Dictionary with revenue details
        """
        revenue_share = (
            db.query(RevenueShare).filter(RevenueShare.course_id == course_id).first()
        )

        if not revenue_share:
            return {
                "total_revenue": Decimal("0.00"),
                "platform_earnings": Decimal("0.00"),
                "instructor_earnings": Decimal("0.00"),
                "total_enrollments": 0,
                "average_sale_price": Decimal("0.00"),
            }

        avg_price = (
            revenue_share.total_revenue / revenue_share.total_enrollments
            if revenue_share.total_enrollments > 0
            else Decimal("0.00")
        )

        return {
            "total_revenue": revenue_share.total_revenue,
            "platform_earnings": revenue_share.platform_earnings,
            "instructor_earnings": revenue_share.instructor_earnings,
            "pending_payout": revenue_share.pending_payout,
            "total_enrollments": revenue_share.total_enrollments,
            "average_sale_price": avg_price,
            "last_sale_date": revenue_share.last_sale_date,
            "platform_fee_percentage": revenue_share.platform_fee_percentage,
            "instructor_percentage": revenue_share.instructor_percentage,
        }

    @staticmethod
    def handle_refund(db: Session, transaction_id: int) -> bool:
        """
        Handle course refund and reverse revenue splits.

        Args:
            db: Database session
            transaction_id: Revenue transaction ID

        Returns:
            True if successful
        """
        transaction = (
            db.query(RevenueTransaction)
            .filter(RevenueTransaction.id == transaction_id)
            .first()
        )

        if not transaction or transaction.is_refunded:
            return False

        # Mark as refunded
        transaction.is_refunded = True
        transaction.refunded_at = datetime.utcnow()
        transaction.refund_amount = transaction.total_amount

        # Reverse revenue share totals
        revenue_share = (
            db.query(RevenueShare)
            .filter(RevenueShare.course_id == transaction.course_id)
            .first()
        )

        if revenue_share:
            revenue_share.total_revenue -= transaction.total_amount
            revenue_share.platform_earnings -= transaction.platform_fee
            revenue_share.instructor_earnings -= transaction.instructor_earnings
            revenue_share.pending_payout -= transaction.instructor_earnings
            revenue_share.total_enrollments -= 1

        db.commit()

        logger.info(
            f"Processed refund for transaction {transaction_id}: ${transaction.total_amount}"
        )

        return True

    @staticmethod
    def get_platform_revenue_summary(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, any]:
        """
        Get platform-wide revenue summary.

        Args:
            db: Database session
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Platform revenue summary
        """
        query = db.query(RevenueTransaction)

        if start_date:
            query = query.filter(RevenueTransaction.created_at >= start_date)
        if end_date:
            query = query.filter(RevenueTransaction.created_at <= end_date)

        transactions = query.all()

        total_revenue = Decimal("0.00")
        platform_earnings = Decimal("0.00")
        instructor_earnings = Decimal("0.00")
        affiliate_commissions = Decimal("0.00")
        total_sales = 0

        for txn in transactions:
            if not txn.is_refunded:
                total_revenue += txn.total_amount
                platform_earnings += txn.platform_fee
                instructor_earnings += txn.instructor_earnings
                affiliate_commissions += txn.affiliate_commission
                total_sales += 1

        return {
            "total_revenue": total_revenue,
            "platform_earnings": platform_earnings,
            "instructor_earnings": instructor_earnings,
            "affiliate_commissions": affiliate_commissions,
            "total_sales": total_sales,
            "average_sale_value": total_revenue / total_sales
            if total_sales > 0
            else Decimal("0.00"),
        }
