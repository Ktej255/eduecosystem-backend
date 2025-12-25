"""
Mastery Level API Endpoints
Track XP, levels, and badges for student progression.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import json

from app.api import deps
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


# ============ SCHEMAS ============

class MasteryStatus(BaseModel):
    level: int
    level_name: str
    current_xp: int
    xp_to_next_level: int
    progress_percent: float
    total_xp: int
    badges: List[dict]
    topics_mastered: int


class XPGainResponse(BaseModel):
    xp_gained: int
    leveled_up: bool
    new_level: int
    new_level_name: str
    new_badges: List[dict]
    current_xp: int
    xp_to_next_level: int


# ============ ENDPOINTS ============

@router.get("/status", response_model=MasteryStatus)
async def get_mastery_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get user's current mastery level and XP"""
    from app.models.mastery import MasteryLevel
    
    mastery = db.query(MasteryLevel).filter(MasteryLevel.user_id == current_user.id).first()
    
    if not mastery:
        # Create initial mastery record
        mastery = MasteryLevel(user_id=current_user.id)
        db.add(mastery)
        db.commit()
        db.refresh(mastery)
    
    badges = json.loads(mastery.badges) if mastery.badges else []
    progress = (mastery.current_xp / mastery.xp_to_next_level) * 100 if mastery.xp_to_next_level > 0 else 0
    
    return MasteryStatus(
        level=mastery.level,
        level_name=mastery.level_name,
        current_xp=mastery.current_xp,
        xp_to_next_level=mastery.xp_to_next_level,
        progress_percent=min(100, progress),
        total_xp=mastery.total_xp,
        badges=badges,
        topics_mastered=mastery.topics_mastered
    )


@router.post("/add-xp", response_model=XPGainResponse)
async def add_xp(
    source: str,
    amount: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Add XP from activity completion"""
    from app.models.mastery import MasteryLevel, XP_REWARDS
    
    mastery = db.query(MasteryLevel).filter(MasteryLevel.user_id == current_user.id).first()
    
    if not mastery:
        mastery = MasteryLevel(user_id=current_user.id)
        db.add(mastery)
    
    # Get XP amount from rewards or use provided amount
    xp = amount if amount else XP_REWARDS.get(source, 5)
    
    result = mastery.add_xp(xp, source)
    db.commit()
    
    return XPGainResponse(
        xp_gained=result["xp_gained"],
        leveled_up=result["leveled_up"],
        new_level=result["new_level"],
        new_level_name=result["new_level_name"],
        new_badges=result["new_badges"],
        current_xp=mastery.current_xp,
        xp_to_next_level=mastery.xp_to_next_level
    )


@router.get("/leaderboard")
async def get_mastery_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get top students by mastery level"""
    from app.models.mastery import MasteryLevel
    
    top = db.query(MasteryLevel).order_by(
        MasteryLevel.level.desc(),
        MasteryLevel.total_xp.desc()
    ).limit(limit).all()
    
    # Get user's rank
    user_mastery = db.query(MasteryLevel).filter(MasteryLevel.user_id == current_user.id).first()
    user_rank = None
    if user_mastery:
        higher = db.query(MasteryLevel).filter(
            (MasteryLevel.level > user_mastery.level) |
            ((MasteryLevel.level == user_mastery.level) & (MasteryLevel.total_xp > user_mastery.total_xp))
        ).count()
        user_rank = higher + 1
    
    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "user_id": m.user_id,
                "level": m.level,
                "level_name": m.level_name,
                "total_xp": m.total_xp
            }
            for i, m in enumerate(top)
        ],
        "your_rank": user_rank,
        "your_level": user_mastery.level if user_mastery else 1
    }


@router.get("/badges")
async def get_available_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get all available badges and which ones user has earned"""
    from app.models.mastery import MasteryLevel, LEVEL_BADGES
    import json
    
    mastery = db.query(MasteryLevel).filter(MasteryLevel.user_id == current_user.id).first()
    earned_badges = json.loads(mastery.badges) if mastery and mastery.badges else []
    earned_ids = [b.get("id") for b in earned_badges if isinstance(b, dict)]
    
    all_badges = []
    for level, badge in LEVEL_BADGES.items():
        all_badges.append({
            **badge,
            "required_level": level,
            "earned": badge["id"] in earned_ids
        })
    
    return {
        "earned_count": len(earned_badges),
        "total_badges": len(LEVEL_BADGES),
        "badges": all_badges
    }


@router.get("/level-info/{level}")
async def get_level_info(level: int):
    """Get info about a specific level"""
    from app.models.mastery import LEVEL_NAMES, LEVEL_BADGES, MasteryLevel
    
    if level < 1 or level > 12:
        raise HTTPException(status_code=400, detail="Level must be between 1 and 12")
    
    mastery = MasteryLevel()  # Just for calculation
    xp_required = mastery._calculate_xp_required(level)
    
    return {
        "level": level,
        "name": LEVEL_NAMES.get(level, f"Level {level}"),
        "xp_required": xp_required,
        "badge": LEVEL_BADGES.get(level),
        "unlocks": LEVEL_UNLOCKS.get(level, [])
    }


# What gets unlocked at each level
LEVEL_UNLOCKS = {
    1: ["Basic meditation processes", "Progress tracking"],
    2: ["Habit tracker", "Streak rewards"],
    3: ["Advanced retention analytics", "Connect the dots"],
    4: ["Midnight test history", "Performance insights"],
    5: ["Premium meditation processes", "Audio review mode"],
    7: ["Peer comparison", "Study groups"],
    10: ["Mentorship access", "Advanced graphotherapy"]
}
