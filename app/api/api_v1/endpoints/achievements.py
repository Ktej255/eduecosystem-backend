"""
Achievement API Endpoints

Provides endpoints for managing and viewing achievements.
"""

from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.achievement import Achievement, AchievementCategory
from app.services.achievement_service import (
    get_predefined_achievements,
    get_user_achievements,
    get_achievement_progress,
)

router = APIRouter()


@router.get("/", response_model=List[dict])
def list_achievements(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    category: str = None,
    show_hidden: bool = False,
) -> Any:
    """
    Get all achievements, optionally filtered by category.
    Hidden achievements are only shown if the user has unlocked them.
    """
    query = db.query(Achievement).filter(Achievement.is_active == True)

    if category:
        query = query.filter(Achievement.category == category)

    achievements = query.order_by(Achievement.display_order).all()

    # Get user's unlocked achievement IDs
    user_unlocked = {ua.achievement_id for ua in current_user.achievements_earned}

    result = []
    for ach in achievements:
        # Skip hidden achievements unless user has unlocked them
        if ach.is_hidden and ach.id not in user_unlocked and not show_hidden:
            continue

        result.append(
            {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "category": ach.category.value
                if hasattr(ach.category, "value")
                else ach.category,
                "rarity": ach.rarity.value
                if hasattr(ach.rarity, "value")
                else ach.rarity,
                "icon": ach.icon,
                "coin_reward": ach.coin_reward,
                "is_hidden": ach.is_hidden,
                "is_unlocked": ach.id in user_unlocked,
                "unlock_condition": ach.unlock_condition,
            }
        )

    return result


@router.get("/my", response_model=List[dict])
def get_my_achievements(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get achievements unlocked by current user.
    """
    user_achievements = get_user_achievements(db, current_user.id)

    result = []
    for ua in user_achievements:
        ach = ua.achievement
        result.append(
            {
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "category": ach.category.value
                if hasattr(ach.category, "value")
                else ach.category,
                "rarity": ach.rarity.value
                if hasattr(ach.rarity, "value")
                else ach.rarity,
                "icon": ach.icon,
                "coin_reward": ach.coin_reward,
                "unlocked_at": ua.unlocked_at.isoformat() if ua.unlocked_at else None,
                "progress": ua.progress,
            }
        )

    return result


@router.get("/progress", response_model=dict)
def get_my_progress(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user's overall achievement progress.
    """
    return get_achievement_progress(db, current_user)


@router.get("/categories", response_model=List[str])
def list_categories() -> Any:
    """
    Get all achievement categories.
    """
    return [cat.value for cat in AchievementCategory]


@router.post("/seed")
def seed_achievements(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Seed predefined achievements (admin only).
    """
    achievements_data = get_predefined_achievements()

    created = 0
    updated = 0

    for data in achievements_data:
        # Check if exists
        existing = (
            db.query(Achievement).filter(Achievement.name == data["name"]).first()
        )

        if existing:
            # Update
            for key, value in data.items():
                setattr(existing, key, value)
            updated += 1
        else:
            # Create
            achievement = Achievement(**data)
            db.add(achievement)
            created += 1

    db.commit()

    return {
        "message": "Achievements seeded successfully",
        "created": created,
        "updated": updated,
        "total": len(achievements_data),
    }
