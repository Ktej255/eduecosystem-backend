from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Any, List, Dict
from datetime import datetime, timedelta
from app.api import deps
from app.models.user import User
from app.models.lead import Lead
from app.models.course_payment import CoursePayment
from app.models.study_session import StudySession
from app.models.drill import DrillSession, DrillQuestion
from app.models.meditation import MeditationSession, MeditationProgress
from app.models.graphotherapy import GraphoSubmission, GraphotherapyProgress
from app.models.activity_log import ActivityLog
from app.models.marketing_automation import MessageLog

router = APIRouter()

@router.get("/{student_id}/journey", response_model=Dict[str, Any])
def get_student_journey(
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    PHASE 1.3 — CROSS-PORTAL STUDENT JOURNEY VIEW
    Unified data aggregator for a single student profile.
    """
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    # 1. Profile & Lead Correlation
    lead = db.query(Lead).filter(Lead.email == user.email).first()
    total_paid = db.query(func.sum(CoursePayment.amount)).filter(
        CoursePayment.user_id == student_id,
        CoursePayment.status == "succeeded"
    ).scalar() or 0.0

    profile = {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "phone": getattr(user, "phone", "N/A"),
        "enrolled_date": user.created_at.isoformat(),
        "lead_source": lead.source if lead else "Organic",
        "lead_status": lead.status if lead else "Enrolled",
        "total_paid": float(total_paid),
        "purchased_subjects": user.purchased_subjects or []
    }

    # 2. Academic Performance (Subject-Wise)
    # Get study hours by subject name
    study_stats = db.query(
        StudySession.subject_name,
        func.sum(StudySession.duration_seconds).label('seconds')
    ).filter(StudySession.user_id == student_id).group_by(StudySession.subject_name).all()
    
    # Get MCQ proficiency by GS Paper (Subject)
    drill_stats = db.query(
        DrillQuestion.gs_paper,
        func.avg(DrillSession.overall_score).label('avg_score'),
        func.count(DrillSession.id).label('count')
    ).join(DrillQuestion, DrillQuestion.id == DrillSession.question_id).filter(
        DrillSession.student_id == student_id
    ).group_by(DrillQuestion.gs_paper).all()

    subject_progress = {}
    for s in study_stats:
        if s.subject_name:
            subject_progress[s.subject_name] = round(s.seconds / 3600, 1) # Hours

    # Calculate composite scores
    total_study_h = float(db.query(func.sum(StudySession.duration_seconds)).filter(StudySession.user_id == student_id).scalar() or 0) / 3600
    mcq_acc_val = float(db.query(func.avg(DrillSession.overall_score)).filter(DrillSession.student_id == student_id).scalar() or 0)
    
    # overall_progress: Weighted average of syllabus breadth and score
    # Simple heuristic: 40% breadth (subjects) + 60% depth (MCQ accuracy)
    breadth_score = min((len(subject_progress) / 6) * 100, 100) # Assuming 6 core subjects
    overall_progress_val = round((breadth_score * 0.4) + (mcq_acc_val * 0.6), 1)

    academic = {
        "overall_progress": float(overall_progress_val),
        "subject_progress": subject_progress,
        "mcq_accuracy": round(mcq_acc_val, 1),
        "mcq_attempted": db.query(func.count(DrillSession.id)).filter(DrillSession.student_id == student_id).scalar() or 0,
        "total_study_hours": round(total_study_h, 1),
        "current_streak": user.streak_days,
        "weak_topics": [d.gs_paper for d in drill_stats if (d.avg_score or 0) < 40],
        "strong_topics": [d.gs_paper for d in drill_stats if (d.avg_score or 0) >= 70]
    }

    # 3. Mindset & Wellness
    med_progress = db.query(MeditationProgress).filter(MeditationProgress.user_id == student_id).first()
    grapho_progress = db.query(GraphotherapyProgress).filter(GraphotherapyProgress.user_id == student_id).first()
    
    med_sessions = db.query(func.count(MeditationSession.id)).filter(MeditationSession.user_id == student_id).scalar() or 0
    grapho_subs = db.query(func.count(GraphoSubmission.id)).filter(GraphoSubmission.user_id == student_id).scalar() or 0
    
    # wellness_score: Combined metric of consistency and depth
    wellness_score_val = min(((med_sessions * 2) + (grapho_subs * 10)), 100)

    wellness = {
        "meditation_sessions_total": med_sessions,
        "meditation_minutes_total": round((db.query(func.sum(MeditationSession.duration_seconds)).filter(MeditationSession.user_id == student_id).scalar() or 0) / 60, 1),
        "meditation_streak": med_progress.total_streak if med_progress else 0,
        "grapho_submissions": grapho_subs,
        "latest_grapho_traits": grapho_progress.completed_days if grapho_progress else {}, 
        "wellness_score": int(wellness_score_val)
    }

    # 4. Timeline (Unified Feed)
    logs = db.query(ActivityLog).filter(ActivityLog.user_id == student_id).order_by(desc(ActivityLog.timestamp)).limit(20).all()
    timeline = []
    for l in logs:
        timeline.append({
            "date": l.timestamp.isoformat(),
            "event_type": l.action,
            "description": f"Performed {l.action}"
        })

    return {
        "profile": profile,
        "academic": academic,
        "wellness": wellness,
        "timeline": timeline
    }
