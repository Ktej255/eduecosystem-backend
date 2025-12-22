from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class CourseReview(Base):
    __tablename__ = "course_reviews"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Review content
    rating = Column(Float, nullable=False)  # 1-5 stars
    title = Column(String)
    review_text = Column(Text)
    helpful_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Moderation
    is_approved = Column(Integer, default=1)  # For content moderation

    # Relationships
    course = relationship("Course", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<CourseReview course_id={self.course_id} rating={self.rating}>"


class ReviewHelpful(Base):
    __tablename__ = "review_helpful"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(
        Integer,
        ForeignKey("course_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint to prevent multiple votes
    __table_args__ = (
        # UniqueConstraint('review_id', 'user_id', name='unique_review_helpful'),
        # We can use a unique index instead if needed, or handle in logic.
        # SQLAlchemy explicit constraint:
        # UniqueConstraint('review_id', 'user_id', name='uix_review_user_helpful'),
    )
