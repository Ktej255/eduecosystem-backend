"""
Analytics Schemas - Response models for analytics data
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import date, datetime


# ===============================
# Instructor Analytics Schemas
# ===============================


class InstructorAnalyticsBase(BaseModel):
    date: date
    total_students: int
    active_students: int
    new_enrollments: int
    completions: int
    avg_progress: float
    avg_quiz_score: float
    total_revenue: float
    new_revenue: float
    discussion_posts: int
    avg_rating: float


class InstructorAnalyticsResponse(InstructorAnalyticsBase):
    id: int
    instructor_id: int
    course_id: int
    quiz_attempts: int
    assignments_submitted: int
    avg_assignment_score: float
    total_time_spent: int
    avg_session_duration: float
    questions_asked: int
    peer_reviews_completed: int
    new_reviews: int

    model_config = ConfigDict(from_attributes=True)


class InstructorOverview(BaseModel):
    total_students: int
    total_revenue: float
    avg_rating: float
    total_courses: int
    trends: List[Dict]


class CoursePerformance(BaseModel):
    course_id: int
    course_title: str
    total_students: int
    completion_rate: float
    avg_progress: float
    avg_rating: float
    revenue: float
    enrollment_trend: List[Dict]


class StudentProgress(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    progress: float
    avg_quiz_score: float
    last_active: Optional[datetime]
    at_risk: bool
    engagement_score: float


class EngagementHeatmap(BaseModel):
    hour: int
    day_of_week: int
    activity_count: int
    avg_session_duration: float


# ===============================
# Student Analytics Schemas
# ===============================


class StudentAnalyticsBase(BaseModel):
    preferred_time_slot: Optional[str]
    avg_session_duration: float
    total_time_spent: int
    sessions_count: int
    completion_rate: float
    avg_quiz_score: float
    engagement_score: float


class StudentAnalyticsResponse(StudentAnalyticsBase):
    id: int
    user_id: int
    course_id: int
    video_completion_rate: float
    reading_completion_rate: float
    quiz_attempts: int
    assignments_completed: int
    avg_assignment_score: float
    discussion_posts: int
    estimated_completion_date: Optional[date]
    estimated_days_to_complete: Optional[int]
    at_risk_flag: bool
    progress_percentile: Optional[float]
    performance_percentile: Optional[float]
    engagement_percentile: Optional[float]
    last_active: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class LearningInsights(BaseModel):
    preferred_time_slot: str
    learning_style: str  # visual, reading, interactive
    study_patterns: Dict
    strengths: List[str]
    areas_for_improvement: List[str]


class ProgressPrediction(BaseModel):
    current_progress: float
    estimated_completion_date: Optional[date]
    estimated_days_remaining: Optional[int]
    on_track: bool
    recommendation: str


class SkillGap(BaseModel):
    skill_name: str
    current_level: float
    target_level: float
    gap_percentage: float
    recommended_resources: List[str]


# ===============================
# Platform Analytics Schemas
# ===============================


class PlatformAnalyticsBase(BaseModel):
    date: date
    total_users: int
    active_users: int
    new_users: int
    dau: int
    mau: int
    total_courses: int
    total_enrollments: int
    total_revenue: float


class PlatformAnalyticsResponse(PlatformAnalyticsBase):
    id: int
    wau: int
    total_students: int
    total_instructors: int
    new_students: int
    new_instructors: int
    active_courses: int
    published_courses: int
    new_courses: int
    enrollments_today: int
    active_enrollments: int
    completions_today: int
    total_completions: int
    revenue_today: float
    revenue_mtd: float
    mrr: float
    arr: float
    quiz_attempts: int
    assignments_submitted: int
    discussion_posts: int
    certificates_issued: int
    avg_course_rating: float
    user_growth_rate: Optional[float]
    revenue_growth_rate: Optional[float]
    enrollment_growth_rate: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class PlatformOverview(BaseModel):
    users: Dict  # total, active, growth_rate
    revenue: Dict  # total, mtd, growth_rate, mrr
    courses: Dict  # total, active, new
    engagement: Dict  # enrollments, completions, avg_rating


class RevenueMetrics(BaseModel):
    total_revenue: float
    revenue_today: float
    revenue_mtd: float
    revenue_ytd: float
    mrr: float
    arr: float
    growth_rate: float
    revenue_by_course: List[Dict]
    revenue_trend: List[Dict]


class UserMetrics(BaseModel):
    total_users: int
    active_users: int
    dau: int
    wau: int
    mau: int
    user_growth_trend: List[Dict]
    user_retention_rate: float
    churn_rate: float


class ContentMetrics(BaseModel):
    total_courses: int
    published_courses: int
    avg_course_rating: float
    most_popular_courses: List[Dict]
    trending_topics: List[str]
    content_gaps: List[str]


# ===============================
# Event Tracking Schemas
# ===============================


class EventCreate(BaseModel):
    event_type: str
    user_id: Optional[int] = None
    course_id: Optional[int] = None
    event_data: Optional[Dict] = None
    session_id: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    event_type: str
    user_id: Optional[int]
    course_id: Optional[int]
    event_data: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ===============================
# Dashboard Schemas
# ===============================


class InstructorDashboard(BaseModel):
    """Complete instructor dashboard data"""

    overview: InstructorOverview
    course_performance: List[CoursePerformance]
    recent_students: List[StudentProgress]
    engagement_heatmap: List[EngagementHeatmap]


class StudentDashboard(BaseModel):
    """Complete student dashboard data"""

    learning_insights: LearningInsights
    progress_prediction: ProgressPrediction
    skill_gaps: List[SkillGap]
    peer_comparison: Dict


class AdminDashboard(BaseModel):
    """Complete admin dashboard data"""

    platform_overview: PlatformOverview
    revenue_metrics: RevenueMetrics
    user_metrics: UserMetrics
    content_metrics: ContentMetrics
