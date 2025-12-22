"""
Analytics Models - Comprehensive platform analytics tracking
"""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class InstructorAnalytics(Base):
    """Daily analytics for instructor courses"""

    __tablename__ = "instructor_analytics"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False, index=True)

    # Student metrics
    total_students = Column(Integer, default=0)
    active_students = Column(Integer, default=0)  # Active in last 7 days
    new_enrollments = Column(Integer, default=0)
    completions = Column(Integer, default=0)
    avg_progress = Column(Float, default=0.0)

    # Performance metrics
    avg_quiz_score = Column(Float, default=0.0)
    quiz_attempts = Column(Integer, default=0)
    assignments_submitted = Column(Integer, default=0)
    avg_assignment_score = Column(Float, default=0.0)

    # Revenue metrics
    total_revenue = Column(Float, default=0.0)
    new_revenue = Column(Float, default=0.0)
    refunds = Column(Integer, default=0)
    refund_amount = Column(Float, default=0.0)

    # Engagement metrics
    total_time_spent = Column(Integer, default=0)  # minutes
    avg_session_duration = Column(Float, default=0.0)  # minutes
    discussion_posts = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    peer_reviews_completed = Column(Integer, default=0)

    # Ratings
    avg_rating = Column(Float, default=0.0)
    new_reviews = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id])
    course = relationship("Course", foreign_keys=[course_id])

    # Unique constraint: one record per instructor per course per day
    __table_args__ = ({"sqlite_autoincrement": True},)


class StudentAnalytics(Base):
    """Analytics for individual student learning patterns"""

    __tablename__ = "student_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    # Learning patterns
    preferred_time_slot = Column(String(20))  # morning/afternoon/evening/night
    avg_session_duration = Column(Float, default=0.0)  # minutes
    total_time_spent = Column(Integer, default=0)  # minutes
    sessions_count = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True))

    # Learning style indicators
    video_completion_rate = Column(Float, default=0.0)
    reading_completion_rate = Column(Float, default=0.0)
    quiz_preference = Column(Float, default=0.0)  # 0-1 score
    discussion_engagement = Column(Float, default=0.0)  # 0-1 score

    # Performance metrics
    completion_rate = Column(Float, default=0.0)
    avg_quiz_score = Column(Float, default=0.0)
    quiz_attempts = Column(Integer, default=0)
    assignments_completed = Column(Integer, default=0)
    avg_assignment_score = Column(Float, default=0.0)

    # Engagement
    discussion_posts = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    peer_reviews_given = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    bookmarks_created = Column(Integer, default=0)

    # Predictions
    estimated_completion_date = Column(Date)
    estimated_days_to_complete = Column(Integer)
    at_risk_flag = Column(Boolean, default=False)
    engagement_score = Column(Float, default=0.0)  # 0-100

    # Peer comparison (percentiles)
    progress_percentile = Column(Float)  # 0-100
    performance_percentile = Column(Float)  # 0-100
    engagement_percentile = Column(Float)  # 0-100

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_calculated = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])


class PlatformAnalytics(Base):
    """Daily platform-wide analytics"""

    __tablename__ = "platform_analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)

    # User metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Active in last 30 days
    new_users = Column(Integer, default=0)
    dau = Column(Integer, default=0)  # Daily active users
    mau = Column(Integer, default=0)  # Monthly active users
    wau = Column(Integer, default=0)  # Weekly active users

    # User roles
    total_students = Column(Integer, default=0)
    total_instructors = Column(Integer, default=0)
    new_students = Column(Integer, default=0)
    new_instructors = Column(Integer, default=0)

    # Course metrics
    total_courses = Column(Integer, default=0)
    active_courses = Column(Integer, default=0)
    published_courses = Column(Integer, default=0)
    new_courses = Column(Integer, default=0)

    # Enrollment metrics
    total_enrollments = Column(Integer, default=0)
    enrollments_today = Column(Integer, default=0)
    active_enrollments = Column(Integer, default=0)
    completions_today = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)

    # Revenue metrics
    revenue_today = Column(Float, default=0.0)
    revenue_mtd = Column(Float, default=0.0)  # Month to date
    total_revenue = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)  # Monthly recurring revenue
    arr = Column(Float, default=0.0)  # Annual recurring revenue

    # Engagement metrics
    quiz_attempts = Column(Integer, default=0)
    assignments_submitted = Column(Integer, default=0)
    discussion_posts = Column(Integer, default=0)
    live_class_attendees = Column(Integer, default=0)
    certificates_issued = Column(Integer, default=0)

    # Content metrics
    total_lessons = Column(Integer, default=0)
    total_quizzes = Column(Integer, default=0)
    total_assignments = Column(Integer, default=0)
    video_hours_watched = Column(Float, default=0.0)

    # Performance metrics
    avg_response_time = Column(Float)  # milliseconds
    error_rate = Column(Float)  # percentage
    uptime = Column(Float, default=99.9)  # percentage

    # Quality metrics
    avg_course_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    new_reviews = Column(Integer, default=0)

    # Growth rates (calculated)
    user_growth_rate = Column(Float)  # percentage
    revenue_growth_rate = Column(Float)  # percentage
    enrollment_growth_rate = Column(Float)  # percentage

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AnalyticsEvent(Base):
    """Real-time event tracking for analytics"""

    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"))

    # Event data (JSON)
    event_data = Column(Text)  # Store as JSON string

    # Metadata
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Event types:
    # - page_view, video_play, video_complete, quiz_start, quiz_complete
    # - assignment_submit, discussion_post, course_enroll, course_complete
    # - purchase, refund, login, logout
