"""
Session Progress API - Save and retrieve CSAT and Evening session progress
Tracks student learning progress across flashcards, Q&A, and CSAT sessions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()


# Request/Response Models
class CSATProgressSave(BaseModel):
    user_id: str
    month: str  # january, february, march
    session_day: int
    video_completed: bool = False
    practice_score: Optional[int] = None
    time_spent_minutes: int = 0


class EveningProgressSave(BaseModel):
    user_id: str
    cycle_id: int
    day: int
    flashcards_total: int = 0
    flashcards_known: int = 0
    flashcards_practice: int = 0
    qa_score: Optional[int] = None
    qa_questions_attempted: int = 0


class ProgressResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# In-memory storage (replace with database in production)
_csat_progress: Dict[str, List[Dict]] = {}
_evening_progress: Dict[str, List[Dict]] = {}


@router.post("/csat/save", response_model=ProgressResponse)
async def save_csat_progress(progress: CSATProgressSave):
    """Save CSAT session progress for a student."""
    
    user_key = f"{progress.user_id}_{progress.month}_{progress.session_day}"
    
    progress_data = {
        "user_id": progress.user_id,
        "month": progress.month,
        "session_day": progress.session_day,
        "video_completed": progress.video_completed,
        "practice_score": progress.practice_score,
        "time_spent_minutes": progress.time_spent_minutes,
        "saved_at": datetime.utcnow().isoformat()
    }
    
    _csat_progress[user_key] = progress_data
    
    return ProgressResponse(
        success=True,
        message="CSAT progress saved successfully",
        data=progress_data
    )


@router.post("/evening/save", response_model=ProgressResponse)
async def save_evening_progress(progress: EveningProgressSave):
    """Save evening session progress (flashcards and Q&A) for a student."""
    
    user_key = f"{progress.user_id}_{progress.cycle_id}_{progress.day}"
    
    progress_data = {
        "user_id": progress.user_id,
        "cycle_id": progress.cycle_id,
        "day": progress.day,
        "flashcards_total": progress.flashcards_total,
        "flashcards_known": progress.flashcards_known,
        "flashcards_practice": progress.flashcards_practice,
        "qa_score": progress.qa_score,
        "qa_questions_attempted": progress.qa_questions_attempted,
        "saved_at": datetime.utcnow().isoformat()
    }
    
    _evening_progress[user_key] = progress_data
    
    return ProgressResponse(
        success=True,
        message="Evening session progress saved successfully",
        data=progress_data
    )


@router.get("/csat/{user_id}")
async def get_csat_progress(user_id: str, month: Optional[str] = None):
    """Get CSAT progress for a user. Optionally filter by month."""
    
    sessions = [
        p for key, p in _csat_progress.items()
        if p.get("user_id") == user_id and (not month or p.get("month") == month)
    ]
    
    # Calculate summary
    completed_videos = sum(1 for p in sessions if p.get("video_completed"))
    scores = [p.get("practice_score", 0) for p in sessions if p.get("practice_score")]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "user_id": user_id,
        "sessions": sessions,
        "summary": {
            "total_sessions": len(sessions),
            "videos_completed": completed_videos,
            "average_score": round(avg_score, 1)
        }
    }


@router.get("/evening/{user_id}")
async def get_evening_progress(user_id: str, cycle_id: Optional[int] = None):
    """Get evening session progress for a user. Optionally filter by cycle."""
    
    sessions = [
        p for key, p in _evening_progress.items()
        if p.get("user_id") == user_id and (not cycle_id or p.get("cycle_id") == cycle_id)
    ]
    
    # Calculate summary
    total_flashcards = sum(p.get("flashcards_total", 0) for p in sessions)
    known_flashcards = sum(p.get("flashcards_known", 0) for p in sessions)
    
    qa_scores = [p.get("qa_score", 0) for p in sessions if p.get("qa_score")]
    avg_qa_score = sum(qa_scores) / len(qa_scores) if qa_scores else 0
    
    return {
        "user_id": user_id,
        "sessions": sessions,
        "summary": {
            "total_sessions": len(sessions),
            "total_flashcards": total_flashcards,
            "known_flashcards": known_flashcards,
            "confidence_rate": round((known_flashcards / total_flashcards * 100) if total_flashcards else 0, 1),
            "average_qa_score": round(avg_qa_score, 1)
        }
    }


@router.get("/dashboard/{user_id}")
async def get_progress_dashboard(user_id: str):
    """Get complete learning progress dashboard for a user."""
    
    csat = await get_csat_progress(user_id)
    evening = await get_evening_progress(user_id)
    
    return {
        "user_id": user_id,
        "csat": csat,
        "evening_sessions": evening,
        "overall": {
            "total_learning_sessions": csat["summary"]["total_sessions"] + evening["summary"]["total_sessions"],
            "csat_completion": f"{csat['summary']['videos_completed']}/30",
            "flashcard_confidence": f"{evening['summary']['confidence_rate']}%"
        }
    }
