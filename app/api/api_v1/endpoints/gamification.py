from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.gamification import Streak, Squad, SquadMember, ActivityType

router = APIRouter()

@router.get("/streaks", response_model=dict)
def get_user_streaks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all streaks for the current user.
    """
    from app.services.gamification_service import gamification_service
    return gamification_service.get_user_streaks(db, current_user.id)

@router.post("/activity/{activity_type}")
def record_activity(
    activity_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Record an activity to update streak
    """
    from app.services.gamification_service import gamification_service
    result = gamification_service.record_activity(db, current_user, activity_type)
    return {
        "status": "success",
        "current_streak": result["current_streak"],
        "global_streak": result["global_streak"]
    }

@router.post("/squads/join")
def join_squad(
    squad_code: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Join a squad by code (name)
    """
    squad = db.query(Squad).filter(Squad.name == squad_code).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
        
    # Check if already member
    member = db.query(SquadMember).filter(
        SquadMember.squad_id == squad.id,
        SquadMember.user_id == current_user.id
    ).first()
    
    if member:
        return {"message": "Already a member"}
        
    new_member = SquadMember(squad_id=squad.id, user_id=current_user.id)
    db.add(new_member)
    db.commit()
    
    return {"status": "joined", "squad_name": squad.name}
