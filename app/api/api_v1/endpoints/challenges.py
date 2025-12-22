"""
Challenge API Endpoints

Provides endpoints for viewing and claiming daily/weekly challenges.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.challenge_service import (
    get_active_challenges_for_user,
    claim_challenge_reward,
)

router = APIRouter()


@router.get("/active", response_model=dict)
def get_active_challenges(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get active daily and weekly challenges for current user.
    """
    challenges = get_active_challenges_for_user(db, current_user)

    # Format response
    result = {"daily": [], "weekly": []}

    for item in challenges["daily"]:
        challenge = item["challenge"]
        progress = item["progress"]

        result["daily"].append(
            {
                "id": challenge.id,
                "title": challenge.title,
                "description": challenge.description,
                "requirement": challenge.requirement,
                "reward_coins": challenge.reward_coins,
                "difficulty": challenge.difficulty,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat(),
                "progress_percentage": progress.progress_percentage,
                "completed": progress.completed_at is not None,
                "completed_at": progress.completed_at.isoformat()
                if progress.completed_at
                else None,
                "reward_claimed": progress.reward_claimed,
                "user_challenge_id": progress.id,
            }
        )

    for item in challenges["weekly"]:
        challenge = item["challenge"]
        progress = item["progress"]

        result["weekly"].append(
            {
                "id": challenge.id,
                "title": challenge.title,
                "description": challenge.description,
                "requirement": challenge.requirement,
                "reward_coins": challenge.reward_coins,
                "difficulty": challenge.difficulty,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat(),
                "progress_percentage": progress.progress_percentage,
                "completed": progress.completed_at is not None,
                "completed_at": progress.completed_at.isoformat()
                if progress.completed_at
                else None,
                "reward_claimed": progress.reward_claimed,
                "user_challenge_id": progress.id,
            }
        )

    return result


@router.post("/{user_challenge_id}/claim", response_model=dict)
def claim_reward(
    user_challenge_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Claim reward for a completed challenge.
    """
    result = claim_challenge_reward(db, current_user, user_challenge_id)

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot claim reward. Challenge not completed, already claimed, or not found.",
        )

    return result
