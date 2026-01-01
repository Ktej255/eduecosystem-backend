from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.learning_group import LearningGroup, HouseType
from app.services.pack_service import pack_service
import json

router = APIRouter()

@router.get("/leaderboard")
def get_pack_leaderboard(
    weekly: bool = False,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get the top packs.
    """
    if weekly:
        packs = pack_service.get_weekly_leaderboard(db, limit)
    else:
        packs = pack_service.get_leaderboard(db, limit)
    
    result = []
    for p in packs:
        metadata = json.loads(p.pack_metadata) if p.pack_metadata else {}
        result.append({
            "id": p.id,
            "name": p.name,
            "house_type": p.house_type,
            "points": p.weekly_points if weekly else p.pack_points,
            "metadata": metadata,
            "is_my_pack": any(m.user_id == current_user.id for m in p.members)
        })
    
    return result

@router.get("/my-pack")
def get_my_pack(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get the current user's primary pack stats.
    """
    # Assuming the first learning group they joined is their primary "Pack"
    # In a more advanced version, we'd have a specific "Pack" designation.
    from app.models.learning_group import GroupMembership
    membership = db.query(GroupMembership).filter(GroupMembership.user_id == current_user.id).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="You are not a member of any Wolf Pack yet.")
    
    pack = db.query(LearningGroup).filter(LearningGroup.id == membership.group_id).first()
    metadata = json.loads(pack.pack_metadata) if pack.pack_metadata else {}
    
    return {
        "id": pack.id,
        "name": pack.name,
        "description": pack.description,
        "house_type": pack.house_type,
        "points": pack.pack_points,
        "weekly_points": pack.weekly_points,
        "metadata": metadata,
        "member_count": len(pack.members)
    }

@router.post("/{group_id}/setup")
def setup_pack(
    group_id: int,
    house_type: HouseType,
    motto: str,
    color: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Admin/Creator tool to set up a group as a Wolf Pack.
    """
    metadata = {
        "motto": motto,
        "color": color,
        "emblem": house_type.upper()[0] # Simple initials for now
    }
    pack = pack_service.set_pack_house_details(db, group_id, house_type, metadata)
    return {"message": "Pack details updated", "pack_id": pack.id}
