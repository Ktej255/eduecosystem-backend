"""
Coin Transaction Models

Provides complete audit trail for all coin transactions.
Tracks earning, spending, and administrative adjustments.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class TransactionType(str, enum.Enum):
    """Types of coin transactions"""

    EARNED = "earned"  # User earned coins
    SPENT = "spent"  # User spent coins
    ADMIN_ADJUSTMENT = "admin_adjustment"  # Manual admin change
    REFUND = "refund"  # Refund from purchase


class CoinTransaction(Base):
    """
    Complete history of all coin transactions for transparency and debugging.
    Every coin change is logged with reason and reference.
    """

    __tablename__ = "coin_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Transaction details
    amount = Column(
        Integer, nullable=False
    )  # Positive for earning, negative for spending
    type = Column(SQLEnum(TransactionType), nullable=False, index=True)

    # Reason/context
    reason = Column(
        String(200), nullable=False
    )  # e.g., "lesson_complete", "quiz_perfect", "shop_purchase"
    description = Column(Text, nullable=True)  # Additional details

    # Reference to related entity (optional)
    # Could be lesson_id, quiz_id, reward_id, etc.
    reference_type = Column(
        String(50), nullable=True
    )  # e.g., "quiz", "lesson", "reward"
    reference_id = Column(Integer, nullable=True)

    # Balance after transaction (for easy tracking)
    balance_after = Column(Integer, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    # user = relationship("User", back_populates="coin_transactions")

    def __repr__(self):
        return f"<CoinTransaction {self.user_id}: {'+' if self.amount > 0 else ''}{self.amount} coins - {self.reason}>"
