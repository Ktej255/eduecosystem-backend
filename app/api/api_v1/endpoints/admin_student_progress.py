from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any, List, Dict
from app.api import deps
from app.models.user import User
from app.models.study_session import StudySession
from app.models.drill import DrillSession, DrillQuestion

router = APIRouter()

@router.get("/{user_id}/progress", response_model=List[Dict[str, Any]])
def get_subject_wise_progress(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Subject-wise Progress: Aggregates MCQ proficiency and Study Hours by Geography, History, etc.
    """
    # 1. Get Study Hours by Subject
    study_stats = db.query(
        StudySession.subject_name,
        func.sum(StudySession.duration_seconds).label('total_seconds')
    ).filter(StudySession.user_id == user_id).group_by(StudySession.subject_name).all()
    
    # 2. Get Drill (MCQ) Performance by Subject
    # We need to join DrillSession with DrillQuestion to get the subject
    drill_stats = db.query(
        DrillQuestion.subject, # Assuming subject exists on question
        func.avg(DrillSession.overall_score).label('avg_score'),
        func.count(DrillSession.id).label('attempts')
    ).join(DrillQuestion, DrillQuestion.id == DrillSession.question_id).filter(
        DrillSession.student_id == user_id
    ).group_by(DrillQuestion.subject).all()
    
    # Combine results
    # Use a set of all subjects found in both
    subjects = set([s.subject_name for s in study_stats if s.subject_name]) | \
               set([d.subject for d in drill_stats if d.subject])
    
    progress = []
    for subject in subjects:
        # Find study hours for this subject
        s_data = next((s for s in study_stats if s.subject_name == subject), None)
        study_hours = round(s_data.total_seconds / 3600, 1) if s_data else 0
        
        # Find drill stats for this subject
        d_data = next((d for d in drill_stats if d.subject == subject), None)
        
        progress.append({
            "subject": subject,
            "study_hours": study_hours,
            "proficiency": round(d_data.avg_score, 1) if d_data else 0,
            "mcq_attempts": d_data.attempts if d_data else 0
        })
        
    return progress
