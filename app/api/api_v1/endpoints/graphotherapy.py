"""
Graphotherapy Progress Tracking Backend
4-Level System with Sequential Day Completion and Image Uploads
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import os
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.graphotherapy import GraphotherapyProgress, GraphotherapyDayCompletion, GRAPHOTHERAPY_LEVELS
from app.schemas.graphotherapy import (
    GraphotherapyProgressResponse,
    LevelInfo,
    LevelDetailResponse,
    DayDetailResponse,
    DayCompleteRequest,
    DayCompleteResponse,
    OverviewResponse,
)

router = APIRouter()

# Upload directory for graphotherapy images
UPLOAD_DIR = "uploads/graphotherapy"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_or_create_progress(db: Session, user_id: int) -> GraphotherapyProgress:
    """Get existing progress or create new one for user"""
    progress = db.query(GraphotherapyProgress).filter(
        GraphotherapyProgress.user_id == user_id
    ).first()
    
    if not progress:
        progress = GraphotherapyProgress(
            user_id=user_id,
            current_level=1,
            current_day=1,
            total_streak=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress


def calculate_streak(progress: GraphotherapyProgress) -> int:
    """Calculate current streak based on last practice date"""
    if not progress.last_practice_date:
        return 0
    
    today = date.today()
    last_practice = progress.last_practice_date.date()
    
    # If practiced today or yesterday, streak is maintained
    if last_practice == today or last_practice == today - timedelta(days=1):
        return progress.total_streak
    else:
        # Streak is broken
        return 0


def is_day_unlocked_by_completion(completion, current_date: date = None) -> bool:
    """
    Check if a completion unlocks the next day.
    The next day is only unlocked if the completion was on a PREVIOUS calendar date.
    This ensures users must wait until midnight (12 AM) for the next day to unlock.
    """
    if completion is None:
        return False
    
    if current_date is None:
        current_date = date.today()
    
    # Get the completion date
    completion_date = completion.completed_at.date()
    
    # Next day is unlocked only if completion was before today (i.e., on a previous day)
    return completion_date < current_date


@router.get("/overview", response_model=OverviewResponse)
def get_graphotherapy_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get overview of graphotherapy progress including all levels"""
    progress = get_or_create_progress(db, current_user.id)
    
    # Get all completions
    completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id
    ).all()
    
    # Build completion map
    completion_map = {}
    for c in completions:
        if c.level not in completion_map:
            completion_map[c.level] = set()
        completion_map[c.level].add(c.day_number)
    
    # Build level info
    levels = []
    total_completed = 0
    total_remaining = 0
    
    for level_num in range(1, 5):
        level_config = GRAPHOTHERAPY_LEVELS[level_num]
        completed_days = len(completion_map.get(level_num, set()))
        total_days = level_config["days"]
        
        is_unlocked = level_num == 1 or (level_num - 1) in completion_map and len(completion_map[level_num - 1]) >= GRAPHOTHERAPY_LEVELS[level_num - 1]["days"]
        is_current = level_num == progress.current_level
        is_completed = completed_days >= total_days
        
        levels.append(LevelInfo(
            level=level_num,
            name=level_config["name"],
            description=level_config["description"],
            total_days=total_days,
            completed_days=completed_days,
            is_unlocked=is_unlocked,
            is_current=is_current,
            is_completed=is_completed
        ))
        
        total_completed += completed_days
        total_remaining += total_days - completed_days
    
    return OverviewResponse(
        current_level=progress.current_level,
        current_day=progress.current_day,
        total_streak=calculate_streak(progress),
        last_practice_date=progress.last_practice_date,
        levels=levels,
        total_days_completed=total_completed,
        total_days_remaining=total_remaining
    )


@router.get("/level/{level_id}", response_model=LevelDetailResponse)
def get_level_detail(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get detailed view of a specific level with all days"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    progress = get_or_create_progress(db, current_user.id)
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    
    # Check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        
        if prev_completions < prev_level_config["days"]:
            raise HTTPException(status_code=403, detail="Complete previous level first")
    
    # Get completions for this level
    completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id
    ).all()
    
    completion_map = {c.day_number: c for c in completions}
    
    # Build days list
    days = []
    today = date.today()
    for day_num in range(1, level_config["days"] + 1):
        completion = completion_map.get(day_num)
        prev_completion = completion_map.get(day_num - 1) if day_num > 1 else None
        
        # Day is unlocked if:
        # - It's day 1, or
        # - Previous day is completed AND was completed on a PREVIOUS calendar date (not today)
        if day_num == 1:
            is_unlocked = True
        elif prev_completion:
            # Check if previous day was completed before today (unlocks after midnight)
            is_unlocked = is_day_unlocked_by_completion(prev_completion, today)
        else:
            is_unlocked = False
        
        # Calculate unlock date for display
        unlock_date = None
        if not is_unlocked and prev_completion:
            # Will unlock tomorrow (the day after completion)
            unlock_date = (prev_completion.completed_at.date() + timedelta(days=1)).isoformat()
        
        days.append({
            "day_number": day_num,
            "is_unlocked": is_unlocked,
            "is_completed": completion is not None,
            "completed_at": completion.completed_at.isoformat() if completion else None,
            "upload_url": completion.upload_url if completion else None,
            "unlock_date": unlock_date
        })
    
    return LevelDetailResponse(
        level=level_id,
        name=level_config["name"],
        description=level_config["description"],
        total_days=level_config["days"],
        days=days
    )


@router.get("/level/{level_id}/day/{day_number}", response_model=DayDetailResponse)
def get_day_detail(
    level_id: int,
    day_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get details for a specific day"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    if day_number < 1 or day_number > level_config["days"]:
        raise HTTPException(status_code=404, detail="Day not found")
    
    progress = get_or_create_progress(db, current_user.id)
    today = date.today()
    
    # Check if day is unlocked
    # Day 1 is always unlocked
    # Other days are unlocked only if previous day was completed on a PREVIOUS calendar date
    is_unlocked = day_number == 1
    prev_completion = None
    if day_number > 1:
        prev_completion = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id,
            GraphotherapyDayCompletion.day_number == day_number - 1
        ).first()
        # Use time-based unlock check
        is_unlocked = is_day_unlocked_by_completion(prev_completion, today)
    
    # Also check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_level_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        if prev_level_completions < prev_level_config["days"]:
            is_unlocked = False
    
    # Get completion info
    completion = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id,
        GraphotherapyDayCompletion.day_number == day_number
    ).first()
    
    # Can complete today if unlocked and not already completed
    can_complete = is_unlocked and completion is None
    
    return DayDetailResponse(
        level=level_id,
        day_number=day_number,
        is_unlocked=is_unlocked,
        is_completed=completion is not None,
        completed_at=completion.completed_at if completion else None,
        upload_url=completion.upload_url if completion else None,
        can_complete_today=can_complete
    )


@router.post("/level/{level_id}/day/{day_number}/complete", response_model=DayCompleteResponse)
async def complete_day(
    level_id: int,
    day_number: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Complete a day by uploading practice image"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    if day_number < 1 or day_number > level_config["days"]:
        raise HTTPException(status_code=404, detail="Day not found")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    progress = get_or_create_progress(db, current_user.id)
    
    # Check if already completed
    existing = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id,
        GraphotherapyDayCompletion.day_number == day_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Day already completed")
    
    # Check if day is unlocked
    if day_number > 1:
        prev_completion = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id,
            GraphotherapyDayCompletion.day_number == day_number - 1
        ).first()
        if not prev_completion:
            raise HTTPException(status_code=403, detail="Complete previous day first")
    
    # Check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_level_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        if prev_level_completions < prev_level_config["days"]:
            raise HTTPException(status_code=403, detail="Complete previous level first")
    
    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{current_user.id}_{level_id}_{day_number}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create upload URL (relative path for serving)
    upload_url = f"/uploads/graphotherapy/{unique_filename}"
    
    # Create completion record
    completion = GraphotherapyDayCompletion(
        progress_id=progress.id,
        level=level_id,
        day_number=day_number,
        upload_url=upload_url,
        upload_filename=file.filename
    )
    db.add(completion)
    
    # Update streak
    today = date.today()
    if progress.last_practice_date:
        last_practice = progress.last_practice_date.date()
        if last_practice == today - timedelta(days=1):
            progress.total_streak += 1
        elif last_practice != today:
            progress.total_streak = 1
    else:
        progress.total_streak = 1
    
    progress.last_practice_date = datetime.now()
    
    # Check if level is completed
    level_completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id
    ).count() + 1  # +1 for current completion
    
    level_completed = level_completions >= level_config["days"]
    next_level_unlocked = level_completed and level_id < 4
    
    # Update current level and day
    if level_completed and level_id < 4:
        progress.current_level = level_id + 1
        progress.current_day = 1
    elif not level_completed:
        progress.current_day = day_number + 1
    
    db.commit()
    
    return DayCompleteResponse(
        success=True,
        message=f"Day {day_number} completed successfully!",
        upload_url=upload_url,
        new_streak=progress.total_streak,
        level_completed=level_completed,
        next_level_unlocked=next_level_unlocked
    )


@router.get("/streak")
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get current streak information"""
    progress = get_or_create_progress(db, current_user.id)
    
    return {
        "current_streak": calculate_streak(progress),
        "total_streak": progress.total_streak,
        "last_practice_date": progress.last_practice_date
    }
