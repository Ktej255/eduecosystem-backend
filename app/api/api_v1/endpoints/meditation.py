"""
Meditation Session System - Student API Endpoints
Progressive Process System with Video Explanations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.meditation import (
    MeditationProcess,
    MeditationProgress,
    MeditationDayCompletion,
    MeditationProcessCompletion,
    MEDITATION_LEVELS,
    get_processes_for_day,
    get_new_processes_for_day,
)
from app.schemas.meditation import (
    MeditationOverviewResponse,
    MeditationLevelInfo,
    MeditationLevelDetailResponse,
    MeditationDayInfo,
    MeditationDayOverview,
    MeditationProcessResponse,
    ProcessCompleteRequest,
    ProcessCompleteResponse,
    DayCompleteRequest,
    DayCompleteResponse,
)

router = APIRouter()


def get_or_create_progress(db: Session, user_id: int) -> MeditationProgress:
    """Get existing progress or create new one for user"""
    progress = db.query(MeditationProgress).filter(
        MeditationProgress.user_id == user_id
    ).first()
    
    if not progress:
        progress = MeditationProgress(
            user_id=user_id,
            current_level=1,
            current_day=1,
            total_streak=0,
            preferred_session="morning"
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress


def calculate_streak(progress: MeditationProgress) -> int:
    """Calculate current streak based on last practice date"""
    if not progress.last_practice_date:
        return 0
    
    today = date.today()
    last_practice = progress.last_practice_date.date()
    
    if last_practice == today or last_practice == today - timedelta(days=1):
        return progress.total_streak
    else:
        return 0


def is_day_unlocked(completion, current_date: date = None) -> bool:
    """Check if next day is unlocked (completion must be on previous date)"""
    if completion is None:
        return False
    if current_date is None:
        current_date = date.today()
    completion_date = completion.completed_at.date()
    return completion_date < current_date


@router.get("/overview", response_model=MeditationOverviewResponse)
def get_meditation_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get overview of meditation progress including all levels"""
    progress = get_or_create_progress(db, current_user.id)
    
    # Get all completions
    completions = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id
    ).all()
    
    # Build completion map by level
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
        level_config = MEDITATION_LEVELS[level_num]
        completed_days = len(completion_map.get(level_num, set()))
        total_days = level_config["days"]
        
        is_unlocked = level_num == 1 or (
            level_num - 1 in completion_map and 
            len(completion_map[level_num - 1]) >= MEDITATION_LEVELS[level_num - 1]["days"]
        )
        is_current = level_num == progress.current_level
        is_completed = completed_days >= total_days
        
        levels.append(MeditationLevelInfo(
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
    
    # Get today's process info
    start_proc, end_proc, is_unlock_day = get_processes_for_day(progress.current_day)
    
    return MeditationOverviewResponse(
        current_level=progress.current_level,
        current_day=progress.current_day,
        total_streak=calculate_streak(progress),
        last_practice_date=progress.last_practice_date,
        preferred_session=progress.preferred_session,
        levels=levels,
        total_days_completed=total_completed,
        total_days_remaining=total_remaining,
        todays_processes=end_proc,
        is_unlock_day=is_unlock_day
    )


@router.get("/level/{level_id}", response_model=MeditationLevelDetailResponse)
def get_level_detail(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get detailed view of a specific level with all days"""
    if level_id not in MEDITATION_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    progress = get_or_create_progress(db, current_user.id)
    level_config = MEDITATION_LEVELS[level_id]
    today = date.today()
    
    # Get completions for this level
    completions = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id,
        MeditationDayCompletion.level == level_id
    ).all()
    
    completion_map = {c.day_number: c for c in completions}
    
    # Build days list
    days = []
    for day_num in range(1, level_config["days"] + 1):
        completion = completion_map.get(day_num)
        prev_completion = completion_map.get(day_num - 1) if day_num > 1 else None
        
        # Unlock logic (same as graphotherapy - next day unlocks after midnight)
        if day_num == 1:
            is_unlocked = True
        elif prev_completion:
            is_unlocked = is_day_unlocked(prev_completion, today)
        else:
            is_unlocked = False
        
        # Get process count for this day
        _, proc_count, _ = get_processes_for_day(day_num)
        
        # Unlock date for display
        unlock_date = None
        if not is_unlocked and prev_completion:
            unlock_date = (prev_completion.completed_at.date() + timedelta(days=1)).isoformat()
        
        days.append(MeditationDayInfo(
            day_number=day_num,
            is_unlocked=is_unlocked,
            is_completed=completion is not None,
            completed_at=completion.completed_at.isoformat() if completion else None,
            unlock_date=unlock_date,
            processes_count=proc_count
        ))
    
    return MeditationLevelDetailResponse(
        level=level_id,
        name=level_config["name"],
        description=level_config["description"],
        total_days=level_config["days"],
        days=days
    )


@router.get("/level/{level_id}/day/{day_number}", response_model=MeditationDayOverview)
def get_day_processes(
    level_id: int,
    day_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get all processes for a specific day with completion status"""
    if level_id not in MEDITATION_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level_config = MEDITATION_LEVELS[level_id]
    if day_number < 1 or day_number > level_config["days"]:
        raise HTTPException(status_code=404, detail="Day not found")
    
    progress = get_or_create_progress(db, current_user.id)
    
    # Get process unlock info for this day
    start_process, end_process, is_unlock_day = get_processes_for_day(day_number)
    new_start, new_end = get_new_processes_for_day(day_number)
    
    # Get all active processes for this level up to the unlocked count
    processes = db.query(MeditationProcess).filter(
        MeditationProcess.level == level_id,
        MeditationProcess.is_active == True,
        MeditationProcess.order <= end_process
    ).order_by(MeditationProcess.order).all()
    
    # Check for existing day completion
    day_completion = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id,
        MeditationDayCompletion.level == level_id,
        MeditationDayCompletion.day_number == day_number
    ).first()
    
    # Get completed processes for today
    completed_process_ids = []
    if day_completion:
        process_completions = db.query(MeditationProcessCompletion).filter(
            MeditationProcessCompletion.day_completion_id == day_completion.id
        ).all()
        completed_process_ids = [pc.process_id for pc in process_completions]
    
    return MeditationDayOverview(
        level=level_id,
        day_number=day_number,
        total_processes=end_process,
        is_unlock_day=is_unlock_day,
        new_process_start=new_start if new_start > 0 else None,
        new_process_end=new_end if new_end > 0 else None,
        processes=[MeditationProcessResponse.model_validate(p) for p in processes],
        completed_processes=completed_process_ids,
        is_day_completed=day_completion is not None and len(completed_process_ids) >= len(processes)
    )


@router.post("/level/{level_id}/day/{day_number}/process/{process_id}/complete")
def complete_process(
    level_id: int,
    day_number: int,
    process_id: int,
    request: ProcessCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Mark a single process as completed"""
    progress = get_or_create_progress(db, current_user.id)
    
    # Get or create day completion record
    day_completion = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id,
        MeditationDayCompletion.level == level_id,
        MeditationDayCompletion.day_number == day_number
    ).first()
    
    if not day_completion:
        day_completion = MeditationDayCompletion(
            progress_id=progress.id,
            level=level_id,
            day_number=day_number,
            session_type="morning"
        )
        db.add(day_completion)
        db.commit()
        db.refresh(day_completion)
    
    # Check if process already completed
    existing = db.query(MeditationProcessCompletion).filter(
        MeditationProcessCompletion.day_completion_id == day_completion.id,
        MeditationProcessCompletion.process_id == process_id
    ).first()
    
    if existing:
        return ProcessCompleteResponse(
            success=True,
            message="Process already completed",
            process_id=process_id,
            all_processes_done=False
        )
    
    # Create process completion
    process_completion = MeditationProcessCompletion(
        day_completion_id=day_completion.id,
        process_id=process_id,
        watched_video=request.watched_video
    )
    db.add(process_completion)
    db.commit()
    
    # Check if all processes are done
    _, total_processes, _ = get_processes_for_day(day_number)
    completed_count = db.query(MeditationProcessCompletion).filter(
        MeditationProcessCompletion.day_completion_id == day_completion.id
    ).count()
    
    all_done = completed_count >= total_processes
    
    return ProcessCompleteResponse(
        success=True,
        message="Process completed!",
        process_id=process_id,
        all_processes_done=all_done
    )


@router.post("/level/{level_id}/day/{day_number}/complete", response_model=DayCompleteResponse)
def complete_day(
    level_id: int,
    day_number: int,
    request: DayCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Complete the entire day (should be called after all processes are done)"""
    progress = get_or_create_progress(db, current_user.id)
    level_config = MEDITATION_LEVELS[level_id]
    
    # Get or update day completion
    day_completion = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id,
        MeditationDayCompletion.level == level_id,
        MeditationDayCompletion.day_number == day_number
    ).first()
    
    if not day_completion:
        day_completion = MeditationDayCompletion(
            progress_id=progress.id,
            level=level_id,
            day_number=day_number,
            session_type=request.session_type,
            notes=request.notes
        )
        db.add(day_completion)
    else:
        day_completion.session_type = request.session_type
        day_completion.notes = request.notes
    
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
    level_completions = db.query(MeditationDayCompletion).filter(
        MeditationDayCompletion.progress_id == progress.id,
        MeditationDayCompletion.level == level_id
    ).count()
    
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
        message=f"Day {day_number} completed!",
        new_streak=progress.total_streak,
        level_completed=level_completed,
        next_level_unlocked=next_level_unlocked
    )
