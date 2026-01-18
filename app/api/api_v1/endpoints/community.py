from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from pydantic import BaseModel
import random 
from datetime import datetime, timedelta

router = APIRouter()

# --- Schemas ---
class UserPresence(BaseModel):
    user_id: int
    name: str
    avatar: str
    status: str # "focusing", "taking_break", "online"
    current_subject: str
    last_seen: datetime

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    name: str
    xp: int
    streak: int
    avatar: str

# --- Mock Data Store (In-Memory for MVP) ---
# In production, use Redis or DB
active_users = {} 

@router.post("/presence")
def update_presence(
    status: str = "focusing",
    subject: str = "General Studies",
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Updates the current user's presence in the library."""
    active_users[current_user.id] = {
        "user_id": current_user.id,
        "name": current_user.full_name or "Student",
        "avatar": current_user.avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={current_user.email}",
        "status": status,
        "current_subject": subject,
        "last_seen": datetime.utcnow()
    }
    return {"msg": "Presence updated"}

@router.get("/presence", response_model=List[UserPresence])
def get_active_users(
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get list of users currently in the library (last 5 mins)."""
    # Clean up old users
    now = datetime.utcnow()
    timeout = timedelta(minutes=5)
    
    # Filter active
    current_active = []
    
    # 1. Add real users
    for uid, data in list(active_users.items()):
        if now - data["last_seen"] < timeout:
            current_active.append(UserPresence(**data))
        else:
            del active_users[uid]
            
    # 2. Add some "Bot" students for ambiance if empty
    if len(current_active) < 5:
        bots = [
            {"user_id": 991, "name": "Aarav", "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Aarav", "status": "focusing", "current_subject": "Polity", "last_seen": now},
            {"user_id": 992, "name": "Vihaan", "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Vihaan", "status": "focusing", "current_subject": "Economy", "last_seen": now},
            {"user_id": 993, "name": "Diya", "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Diya", "status": "taking_break", "current_subject": "Rest", "last_seen": now},
        ]
        available_bots = [b for b in bots if b["user_id"] not in active_users]
        for b in available_bots:
             current_active.append(UserPresence(**b))
    
    return current_active

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    db: Session = Depends(deps.get_db),
) -> Any:
    """Get top 10 students by XP."""
    # TODO: Query actual User table for XP
    # For now, return mock consistent leaderboard + current user
    
    leaderboard = [
        {"rank": 1, "user_id": 101, "name": "Sidharth M.", "xp": 15400, "streak": 45, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sid"},
        {"rank": 2, "user_id": 102, "name": "Tara S.", "xp": 14200, "streak": 32, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Tara"},
        {"rank": 3, "user_id": 103, "name": "Rohan K.", "xp": 12800, "streak": 28, "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Rohan"},
    ]
    
    return [LeaderboardEntry(**entry) for entry in leaderboard]
