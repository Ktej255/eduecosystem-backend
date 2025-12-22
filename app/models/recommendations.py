"""
User Behavior Tracking Models
Track user interactions for recommendation engine
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class UserActivity(Base):
    """Track user activities for recommendations"""

    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_type = Column(
        String, nullable=False
    )  # view, enroll, complete, rate, bookmark
    target_type = Column(String, nullable=False)  # course, lesson, quiz
    target_id = Column(Integer, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="activities")


class CourseRecommendation(Base):
    """Store pre-computed course recommendations"""

    __tablename__ = "course_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    score = Column(Float, nullable=False)  # Recommendation confidence score
    reason = Column(String, nullable=True)  # Why this was recommended
    algorithm = Column(String, nullable=False)  # collaborative, content-based, hybrid
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    clicked = Column(DateTime, nullable=True)  # Track if user clicked
    enrolled = Column(DateTime, nullable=True)  # Track if user enrolled

    # Relationships
    user = relationship("User", backref="recommendations")
    course = relationship("Course", backref="recommendations")


class UserPreference(Base):
    """Store user learning preferences"""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    preferred_categories = Column(JSON, nullable=True)  # List of category IDs
    preferred_difficulty = Column(
        String, nullable=True
    )  # beginner, intermediate, advanced
    preferred_duration = Column(String, nullable=True)  # short, medium, long
    learning_goals = Column(JSON, nullable=True)  # List of goal strings
    interests = Column(JSON, nullable=True)  # List of interest keywords
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences", uselist=False)
