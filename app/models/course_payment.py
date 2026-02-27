"""
Course Payment Model
Tracks course purchases and payment transactions
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class CoursePayment(Base):
    __tablename__ = "course_payments"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    enrollment_id = Column(
        Integer, ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True
    )

    # Payment details
    amount = Column(Float, nullable=False)  # Amount paid
    currency = Column(String, default="INR")  # Changed default to INR
    status = Column(String, nullable=False)  # pending, succeeded, failed, refunded

    # Payment provider (Now strictly Cashfree)
    gateway = Column(String, default="cashfree", nullable=False)
    
    # Cashfree tracking details
    cashfree_order_id = Column(String, unique=True, index=True, nullable=True)
    cashfree_payment_id = Column(String, unique=True, index=True, nullable=True)
    invoice_url = Column(String, nullable=True)

    # Metadata
    payment_method = Column(String)  # card, paypal, etc.
    failure_reason = Column(Text, nullable=True)
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    succeeded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="course_payments")
    course = relationship("Course", foreign_keys=[course_id])
    enrollment = relationship("Enrollment", foreign_keys=[enrollment_id])
