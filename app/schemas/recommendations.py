"""
Recommendations Pydantic Schemas
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# User Activity Schemas
class UserActivityCreate(BaseModel):
    activity_type: str
    target_type: str
    target_id: int
    metadata: Optional[Dict[str, Any]] = None


class UserActivity(UserActivityCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# User Preference Schemas
class UserPreferenceUpdate(BaseModel):
    preferred_categories: Optional[List[int]] = None
    preferred_difficulty: Optional[str] = None
    preferred_duration: Optional[str] = None
    learning_goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class UserPreference(UserPreferenceUpdate):
    id: int
    user_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Recommendation Schemas
class CourseRecommendationResponse(BaseModel):
    """Single course recommendation"""

    course_id: int
    course_title: str
    course_description: Optional[str]
    instructor_name: str
    category: Optional[str]
    level: Optional[str]
    price: float
    average_rating: Optional[float]
    enrollment_count: int
    score: float
    reasons: List[str]
    thumbnail_url: Optional[str] = None


class RecommendationsResponse(BaseModel):
    """List of recommendations"""

    recommendations: List[CourseRecommendationResponse]
    total: int
    algorithm: str
