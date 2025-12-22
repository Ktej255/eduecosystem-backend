from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/for-you")
def get_personalized_recommendations(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get personalized course recommendations for current user
    """
    service = RecommendationService(db)
    recommendations = service.get_personalized_recommendations(
        user_id=current_user.id, limit=limit
    )

    return {"recommendations": recommendations, "total": len(recommendations)}


@router.get("/similar/{course_id}")
def get_similar_courses(
    course_id: int,
    limit: int = Query(default=5, le=20),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get courses similar to the specified course
    """
    service = RecommendationService(db)
    similar = service.get_similar_courses(course_id=course_id, limit=limit)

    return {"similar_courses": similar, "total": len(similar)}


@router.get("/trending")
def get_trending_courses(
    limit: int = Query(default=10, le=50),
    days: int = Query(default=7, le=30),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get trending courses based on recent enrollment activity
    """
    service = RecommendationService(db)
    trending = service.get_trending_courses(limit=limit, days=days)

    return {"trending_courses": trending, "total": len(trending), "period_days": days}


@router.get("/preferences")
def get_user_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's learning preferences
    """
    from app.models.recommendations import UserPreference

    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )

    if not prefs:
        return {
            "preferred_categories": [],
            "preferred_difficulty": None,
            "preferred_duration": None,
            "learning_goals": [],
            "interests": [],
        }

    return {
        "preferred_categories": prefs.preferred_categories or [],
        "preferred_difficulty": prefs.preferred_difficulty,
        "preferred_duration": prefs.preferred_duration,
        "learning_goals": prefs.learning_goals or [],
        "interests": prefs.interests or [],
    }


@router.put("/preferences")
def update_user_preferences(
    preferred_categories: List[int] = [],
    preferred_difficulty: str = None,
    preferred_duration: str = None,
    learning_goals: List[str] = [],
    interests: List[str] = [],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update user learning preferences
    """
    from app.models.recommendations import UserPreference

    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )

    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)

    prefs.preferred_categories = preferred_categories
    prefs.preferred_difficulty = preferred_difficulty
    prefs.preferred_duration = preferred_duration
    prefs.learning_goals = learning_goals
    prefs.interests = interests

    db.commit()

    return {"message": "Preferences updated successfully"}


@router.post("/track-activity")
def track_user_activity(
    activity_type: str,
    target_type: str,
    target_id: int,
    meta_data: dict = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Track user activity for recommendation engine
    activity_type: view, enroll, complete, rate, bookmark
    target_type: course, lesson, quiz
    """
    from app.models.recommendations import UserActivity

    activity = UserActivity(
        user_id=current_user.id,
        activity_type=activity_type,
        target_type=target_type,
        target_id=target_id,
        meta_data=meta_data,
    )

    db.add(activity)
    db.commit()

    return {"message": "Activity tracked"}
