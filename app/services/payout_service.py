"""
Payout Service

Business logic for instructor and affiliate payout processing.
Handles payout requests, Stripe Connect integration, and payment tracking.
"""

from sqlalchemy.orm import Session
from app.models.marketplace import InstructorPayout, InstructorPaymentInfo, RevenueShare
from app.models.affiliate import AffiliatePayout
from decimal import Decimal
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class PayoutService:
    """Service for processing instructor and affiliate payouts."""

    # Minimum payout thresholds
    MIN_INSTRUCTOR_PAYOUT = Decimal("50.00")
    MIN_AFFILIATE_PAYOUT = Decimal("50.00")

    @staticmethod
    def request_instructor_payout(
        db: Session,
        instructor_id: int,
        amount: Optional[Decimal] = None,
        payment_method: str = "stripe",
    ) -> InstructorPayout:
        """
        Create instructor payout request.

        Args:
            db: Database session
            instructor_id: Instructor ID
            amount: Amount to payout (None = all pending)
            payment_method: Payment method (stripe, paypal, bank_transfer)

        Returns:
            InstructorPayout instance

        Raises:
            ValueError: If insufficient balance or invalid request
        """
        # Get payment info
        payment_info = (
            db.query(InstructorPaymentInfo)
            .filter(InstructorPaymentInfo.instructor_id == instructor_id)
            .first()
        )

        if not payment_info:
            raise ValueError("Payment information not configured")

        if not payment_info.verified:
            raise ValueError("Payment information not verified")

        # Calculate available balance
        revenue_shares = (
            db.query(RevenueShare)
            .filter(RevenueShare.instructor_id == instructor_id)
            .all()
        )

        available_balance = sum(share.pending_payout for share in revenue_shares)

        # Determine payout amount
        payout_amount = amount if amount else available_balance

        # Validate amount
        if payout_amount < PayoutService.MIN_INSTRUCTOR_PAYOUT:
            raise ValueError(
                f"Minimum payout is ${PayoutService.MIN_INSTRUCTOR_PAYOUT}"
            )

        if payout_amount > available_balance:
            raise ValueError(f"Insufficient balance. Available: ${available_balance}")

        # Create payout request
        payout = InstructorPayout(
            instructor_id=instructor_id,
            amount=payout_amount,
            payment_method=payment_method,
            status="pending",
        )

        db.add(payout)
        db.commit()
        db.refresh(payout)

        logger.info(f"Instructor {instructor_id} requested payout: ${payout_amount}")

        return payout

    @staticmethod
    async def process_instructor_payout(
        db: Session, payout_id: int, admin_id: Optional[int] = None
    ) -> bool:
        """
        Process instructor payout via Stripe Connect.

        Args:
            db: Database session
            payout_id: Payout request ID
            admin_id: Admin approving payout

        Returns:
            True if successful
        """
        payout = (
            db.query(InstructorPayout).filter(InstructorPayout.id == payout_id).first()
        )

        if not payout or payout.status != "pending":
            return False

        # Update status
        payout.status = "processing"
        payout.processed_at = datetime.utcnow()
        db.commit()

        try:
            # Get payment info
            payment_info = (
                db.query(InstructorPaymentInfo)
                .filter(InstructorPaymentInfo.instructor_id == payout.instructor_id)
                .first()
            )

            if payout.payment_method == "stripe" and payment_info.stripe_account_id:
                # Process via Stripe Connect
                transfer_id = await PayoutService._process_stripe_transfer(
                    payment_info.stripe_account_id, payout.amount
                )
                payout.stripe_transfer_id = transfer_id
                payout.transaction_id = transfer_id

            elif payout.payment_method == "paypal" and payment_info.paypal_email:
                # Process via PayPal (placeholder)
                transaction_id = await PayoutService._process_paypal_payout(
                    payment_info.paypal_email, payout.amount
                )
                payout.transaction_id = transaction_id

            else:
                raise Exception("Invalid payment method configuration")

            # Mark as completed
            payout.status = "completed"
            payout.completed_at = datetime.utcnow()

            # Deduct from pending payouts
            revenue_shares = (
                db.query(RevenueShare)
                .filter(RevenueShare.instructor_id == payout.instructor_id)
                .all()
            )

            remaining = payout.amount
            for share in revenue_shares:
                if remaining <= 0:
                    break

                deduction = min(share.pending_payout, remaining)
                share.pending_payout -= deduction
                share.last_payout_date = datetime.utcnow()
                remaining -= deduction

            db.commit()

            logger.info(f"Completed payout {payout_id}: ${payout.amount}")

            return True

        except Exception as e:
            payout.status = "failed"
            payout.failure_reason = str(e)
            db.commit()

            logger.error(f"Payout {payout_id} failed: {e}")

            return False

    @staticmethod
    async def _process_stripe_transfer(stripe_account_id: str, amount: Decimal) -> str:
        """
        Process Stripe Connect transfer.

        Args:
            stripe_account_id: Stripe Connect account ID
            amount: Transfer amount

        Returns:
            Transfer ID
        """
        try:
            import stripe

            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

            # Convert to cents
            amount_cents = int(amount * 100)

            # Create transfer
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=stripe_account_id,
                description="Instructor earnings payout",
            )

            return transfer.id

        except Exception as e:
            logger.error(f"Stripe transfer failed: {e}")
            raise

    @staticmethod
    async def _process_paypal_payout(paypal_email: str, amount: Decimal) -> str:
        """
        Process PayPal payout (placeholder).

        Args:
            paypal_email: PayPal email
            amount: Payout amount

        Returns:
            Transaction ID
        """
        # TODO: Implement PayPal Payouts API integration
        logger.info(f"PayPal payout to {paypal_email}: ${amount}")
        return f"PAYPAL_{datetime.utcnow().timestamp()}"

    @staticmethod
    def get_instructor_payout_history(
        db: Session, instructor_id: int, limit: int = 20
    ) -> List[InstructorPayout]:
        """
        Get instructor payout history.

        Args:
            db: Database session
            instructor_id: Instructor ID
            limit: Max results

        Returns:
            List of payouts
        """
        return (
            db.query(InstructorPayout)
            .filter(InstructorPayout.instructor_id == instructor_id)
            .order_by(InstructorPayout.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def process_automatic_payouts(db: Session) -> List[int]:
        """
        Process automatic monthly payouts for eligible instructors.

        Args:
            db: Database session

        Returns:
            List of payout IDs created
        """
        # Find instructors with automatic payout enabled
        payment_infos = (
            db.query(InstructorPaymentInfo)
            .filter(
                InstructorPaymentInfo.verified == True,
                InstructorPaymentInfo.payout_frequency == "monthly",
            )
            .all()
        )

        payout_ids = []

        for info in payment_infos:
            # Check if payout is due
            last_payout = (
                db.query(InstructorPayout)
                .filter(
                    InstructorPayout.instructor_id == info.instructor_id,
                    InstructorPayout.status == "completed",
                )
                .order_by(InstructorPayout.completed_at.desc())
                .first()
            )

            # Skip if payout was made in last 30 days
            if last_payout and last_payout.completed_at > datetime.utcnow() - timedelta(
                days=30
            ):
                continue

            # Calculate available balance
            revenue_shares = (
                db.query(RevenueShare)
                .filter(RevenueShare.instructor_id == info.instructor_id)
                .all()
            )

            available_balance = sum(share.pending_payout for share in revenue_shares)

            # Create payout if above minimum
            if available_balance >= info.minimum_payout_amount:
                try:
                    payout = PayoutService.request_instructor_payout(
                        db,
                        info.instructor_id,
                        available_balance,
                        "stripe",  # Default to Stripe
                    )
                    payout_ids.append(payout.id)
                except Exception as e:
                    logger.error(
                        f"Auto-payout failed for instructor {info.instructor_id}: {e}"
                    )

        logger.info(f"Created {len(payout_ids)} automatic payouts")

        return payout_ids

    @staticmethod
    def get_pending_payouts(
        db: Session,
        payout_type: str = "instructor",  # instructor or affiliate
    ) -> List:
        """
        Get all pending payout requests for admin review.

        Args:
            db: Database session
            payout_type: Type of payout

        Returns:
            List of pending payouts
        """
        if payout_type == "instructor":
            return (
                db.query(InstructorPayout)
                .filter(InstructorPayout.status == "pending")
                .order_by(InstructorPayout.requested_at)
                .all()
            )
        else:
            return (
                db.query(AffiliatePayout)
                .filter(AffiliatePayout.status == "pending")
                .order_by(AffiliatePayout.requested_at)
                .all()
            )

    @staticmethod
    def get_payout_statistics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, any]:
        """
        Get payout statistics for reporting.

        Args:
            db: Database session
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Payout statistics
        """
        query = db.query(InstructorPayout)

        if start_date:
            query = query.filter(InstructorPayout.completed_at >= start_date)
        if end_date:
            query = query.filter(InstructorPayout.completed_at <= end_date)

        completed_payouts = query.filter(InstructorPayout.status == "completed").all()

        total_paid = sum(p.amount for p in completed_payouts)
        total_count = len(completed_payouts)

        pending_payouts = (
            db.query(InstructorPayout)
            .filter(InstructorPayout.status == "pending")
            .all()
        )

        pending_amount = sum(p.amount for p in pending_payouts)

        return {
            "total_paid": total_paid,
            "total_payouts": total_count,
            "average_payout": total_paid / total_count
            if total_count > 0
            else Decimal("0.00"),
            "pending_amount": pending_amount,
            "pending_count": len(pending_payouts),
        }
