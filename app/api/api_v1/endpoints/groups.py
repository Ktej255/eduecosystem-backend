from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.services.grouping import assign_user_to_group
from pydantic import BaseModel

router = APIRouter()


class GroupMember(BaseModel):
    full_name: str
    streak_days: int


class GroupOut(BaseModel):
    id: int
    name: str
    description: str
    members: List[GroupMember]


@router.post("/join", response_model=GroupOut)
def join_pack(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Assign current user to a Wolf Pack.
    """
    group = assign_user_to_group(db, current_user)
    members = [
        GroupMember(full_name=m.full_name or "Unknown", streak_days=m.streak_days)
        for m in group.members
    ]
    return GroupOut(
        id=group.id, name=group.name, description=group.description, members=members
    )


@router.get("/my-group")
def get_my_group(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's group with stats.
    """
    if not current_user.group:
        return {"group": None}

    group = current_user.group
    members_count = len(group.members)
    avg_streak = (
        sum(m.streak_days for m in group.members) / members_count
        if members_count > 0
        else 0
    )
    total_coins = sum(m.coins for m in group.members)

    # Calculate actual rank based on total coins
    from app.models.group import Group

    # Get all groups with their total coins
    all_groups = db.query(Group).all()
    group_scores = []
    for g in all_groups:
        if len(g.members) > 0:
            total_coins = sum(m.coins for m in g.members)
            group_scores.append((g.id, total_coins))

    # Sort by total coins descending
    group_scores.sort(key=lambda x: x[1], reverse=True)

    # Find rank
    rank = 1
    for idx, (gid, score) in enumerate(group_scores):
        if gid == group.id:
            rank = idx + 1
            break

    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "member_count": members_count,
        "avg_streak": round(avg_streak, 1),
        "total_coins": total_coins,
        "rank": rank,
    }


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(deps.get_db), limit: int = 10) -> Any:
    """
    Get Wolf Pack leaderboard.
    """
    from app.models.group import Group

    groups = db.query(Group).all()

    leaderboard = []
    for group in groups:
        members_count = len(group.members)
        if members_count == 0:
            continue

        avg_streak = sum(m.streak_days for m in group.members) / members_count
        total_coins = sum(m.coins for m in group.members)

        leaderboard.append(
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "members": members_count,
                "avgStreak": round(avg_streak, 1),
                "totalCoins": total_coins,
            }
        )

    # Sort by total coins descending
    leaderboard.sort(key=lambda x: x["totalCoins"], reverse=True)

    # Add ranks
    for i, group in enumerate(leaderboard[:limit]):
        group["rank"] = i + 1

    return leaderboard[:limit]
