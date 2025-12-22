from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class PeerReviewStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    OVERDUE = "overdue"


class PeerReviewAssignment(Base):
    """
    Represents an assignment of a student (reviewer) to review another student's submission (reviewee).
    """

    __tablename__ = "peer_review_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)

    status = Column(String, default=PeerReviewStatus.PENDING)
    due_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    assignment = relationship("Assignment")
    reviewer = relationship(
        "User", foreign_keys=[reviewer_id], backref="peer_reviews_to_give"
    )
    reviewee = relationship(
        "User", foreign_keys=[reviewee_id], backref="peer_reviews_received"
    )
    submission = relationship("Submission")
    review = relationship("PeerReview", back_populates="assignment_link", uselist=False)


class PeerReview(Base):
    """
    The actual review content submitted by the reviewer.
    """

    __tablename__ = "peer_reviews"

    id = Column(Integer, primary_key=True, index=True)
    peer_review_assignment_id = Column(
        Integer, ForeignKey("peer_review_assignments.id"), unique=True, nullable=False
    )

    content = Column(Text, nullable=False)  # The written feedback
    score = Column(Float, nullable=True)  # Optional numeric score

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    assignment_link = relationship("PeerReviewAssignment", back_populates="review")
