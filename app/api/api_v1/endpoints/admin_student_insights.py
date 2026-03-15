from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User
from app.models.lead import Lead
from app.models.course_payment import CoursePayment
from app.models.study_session import StudySession
from app.models.drill import DrillSession
from app.models.meditation import MeditationProgress, MeditationSession
from app.models.activity_log import ActivityLog

router = APIRouter()

@router.get("/risk-report", response_model=List[Dict[str, Any]])
def get_at_risk_students(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Automated identification of students at risk of failing or dropping out.
    Criteria: 
    - Average MCQ Score < 50%
    - No Meditation in 3 days
    - No study activity in 5 days
    """
    now = datetime.utcnow()
    risk_list = []
    
    # Get all students
    students = db.query(User).filter(User.role == "student", User.is_active == True).all()
    
    for student in students:
        risk_factors = []
        
        # 1. Academic Risk (MCQ Scores)
        avg_score = db.query(func.avg(DrillSession.overall_score)).filter(
            DrillSession.student_id == student.id
        ).scalar() or 0
        if avg_score < 50 and avg_score > 0:
            risk_factors.append({"factor": "Low Academic Performance", "detail": f"Avg Score: {round(avg_score, 1)}%"})
            
        # 2. Wellness Risk (Meditation)
        last_meditation = db.query(MeditationSession.created_at).filter(
            MeditationSession.user_id == student.id
        ).order_by(desc(MeditationSession.created_at)).first()
        
        if not last_meditation or (now - last_meditation[0]) > timedelta(days=3):
            risk_factors.append({"factor": "Mental Health/Focus Drop", "detail": "No meditation in 3+ days"})
            
        # 3. Churn Risk (Inactivity)
        last_activity = db.query(ActivityLog.timestamp).filter(
            ActivityLog.user_id == student.id
        ).order_by(desc(ActivityLog.timestamp)).first()
        
        if not last_activity or (now - last_activity[0]) > timedelta(days=5):
            risk_factors.append({"factor": "High Churn Risk", "detail": "Inactive for 5+ days"})

        if risk_factors:
            risk_list.append({
                "id": student.id,
                "name": student.full_name or student.email,
                "risk_score": len(risk_factors),
                "factors": risk_factors,
                "last_active": last_activity[0].isoformat() if last_activity else "Never"
            })
            
    # Sort by highest risk
    return sorted(risk_list, key=lambda x: x['risk_score'], reverse=True)

@router.get("/journey/{user_id}", response_model=Dict[str, Any])
def get_student_journey(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    The 'Single View' of a student's journey from Lead to Performer.
    """
    student = db.query(User).filter(User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    timeline = []
    
    # 1. Birth: Lead Creation
    lead = db.query(Lead).filter(Lead.email == student.email).first()
    if lead:
        timeline.append({
            "event": "LEAD_CREATED",
            "date": lead.created_at.isoformat(),
            "details": f"Source: {lead.source_primary or 'Direct'}"
        })
        
    # 2. Conversion: Successful Payments
    payments = db.query(CoursePayment).filter(
        CoursePayment.user_id == user_id, 
        CoursePayment.status == "succeeded"
    ).all()
    for p in payments:
        timeline.append({
            "event": "CONVERTED",
            "date": p.succeeded_at.isoformat(),
            "details": f"Purchased Course ID: {p.course_id} (Amount: {p.amount})"
        })
        
    # 3. Academic Milestones: First MCQ
    first_drill = db.query(DrillSession).filter(DrillSession.student_id == user_id).order_by(DrillSession.created_at).first()
    if first_drill:
        timeline.append({
            "event": "FIRST_MCQ",
            "date": first_drill.created_at.isoformat(),
            "details": f"Initial Score: {first_drill.overall_score}%"
        })

    # Sort timeline by date
    timeline.sort(key=lambda x: x['date'])
    
    return {
        "student_info": {
            "name": student.full_name,
            "email": student.email,
            "joined": student.created_at.isoformat(),
            "streak": student.streak_days
        },
        "timeline": timeline
    }
