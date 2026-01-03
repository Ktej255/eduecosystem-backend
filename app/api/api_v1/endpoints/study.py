from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import base64
import logging

from app.api import deps
from app.db.session import get_db
from app.models.study_session import StudySession
from app.models.user import User
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/sessions/record")
async def record_session(
    email: str = Form(...),
    session_type: str = Form(...),
    topic_id: Optional[str] = Form(None),
    topic_name: Optional[str] = Form(None),
    subject_id: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    duration_seconds: int = Form(...),
    cycle_number: int = Form(1),
    phase_number: int = Form(1),
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Record a completed study session (study or explanation).
    If it's an explanation session and audio is provided, it performs AI analysis.
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Parse timestamps
    try:
        # Expected format: ISO string (e.g. 2023-10-27T10:00:00.000Z)
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"Timestamp parsing error: {e}. Using current time.")
        start_dt = datetime.utcnow()
        end_dt = datetime.utcnow()

    session = StudySession(
        user_id=user.id,
        topic_id=topic_id,
        topic_name=topic_name,
        subject_id=subject_id,
        subject_name=subject_name,
        session_type=session_type,
        start_time=start_dt,
        end_time=end_dt,
        duration_seconds=duration_seconds,
        cycle_number=cycle_number,
        phase_number=phase_number
    )

    # Handle Audio Transcript & AI Analysis
    analysis_result = None
    transcript = None
    
    if audio and session_type.startswith("explanation"):
        try:
            audio_content = await audio.read()
            audio_b64 = base64.b64encode(audio_content).decode("utf-8")
            
            # 1. Transcribe audio
            transcript = gemini_service.transcribe_audio(audio_b64)
            session.audio_transcript = transcript
            
            # 2. Evaluate recall/explanation
            # We use topic_name as the context for recall evaluation
            if topic_name:
                analysis_result = gemini_service.evaluate_recall(
                    original_text=f"Topic: {topic_name}",
                    student_recall=transcript
                )
                session.ai_analysis = analysis_result
                session.comprehension_score = analysis_result.get("score", 0)
        except Exception as e:
            logger.error(f"Error during audio analysis: {e}")
            analysis_result = {"error": "AI analysis failed", "score": 0}

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "success": True,
        "session_id": session.id,
        "analysis": analysis_result,
        "transcript": transcript,
        "score": session.comprehension_score
    }

@router.get("/sessions/stats/{email}")
async def get_study_stats(email: str, db: Session = Depends(get_db)):
    """
    Get aggregated study statistics for a user.
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    sessions = db.query(StudySession).filter(StudySession.user_id == user.id).all()
    
    total_seconds = sum(s.duration_seconds for s in sessions)
    study_sessions_count = len([s for s in sessions if "study" in s.session_type])
    explanation_count = len([s for s in sessions if "explanation" in s.session_type])
    revision_count = len([s for s in sessions if "revision" in s.session_type])
    
    # Calculate average score for explanations
    scores = [s.comprehension_score for s in sessions if s.comprehension_score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Group by subject
    subjects_data = {}
    for s in sessions:
        if s.subject_name:
            if s.subject_name not in subjects_data:
                subjects_data[s.subject_name] = 0
            subjects_data[s.subject_name] += s.duration_seconds
    
    return {
        "overall": {
            "total_hours": round(total_seconds / 3600, 2),
            "study_sessions": study_sessions_count,
            "explanations": explanation_count,
            "revisions": revision_count,
            "average_comprehension": round(avg_score, 1)
        },
        "subjects": [
            {"name": name, "hours": round(dur / 3600, 2)}
            for name, dur in subjects_data.items()
        ]
    }

@router.get("/sessions/history/{email}")
async def get_session_history(email: str, db: Session = Depends(get_db), limit: int = 50):
    """
    Get recent session history for a user.
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    sessions = db.query(StudySession)\
        .filter(StudySession.user_id == user.id)\
        .order_by(StudySession.start_time.desc())\
        .limit(limit)\
        .all()
        
    return [
        {
            "id": s.id,
            "session_type": s.session_type,
            "topic_name": s.topic_name,
            "subject_name": s.subject_name,
            "duration": s.duration_seconds,
            "score": s.comprehension_score,
            "start_time": s.start_time.isoformat(),
            "transcript": s.audio_transcript
        }
        for s in sessions
    ]
