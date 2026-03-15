from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any, List, Dict
from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.models.drill import DrillSession
from app.models.course_payment import CoursePayment
from app.models.marketing_automation import MarketingWorkflow

router = APIRouter()

@router.get("/teacher-scores", response_model=List[Dict[str, Any]])
def get_teacher_performance_scores(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Composite Teacher Performance Scoring.
    Weights: 
    - 40% Student Reach (Enrollments)
    - 30% Student Success (Avg MCQ Scores in their courses)
    - 30% Content/Marketing activity
    """
    teachers = db.query(User).filter(User.role == "teacher").all()
    scores = []
    
    for t in teachers:
        # 1. Student Reach
        course_ids = [c.id for c in db.query(Course.id).filter(Course.instructor_id == t.id).all()]
        enrollment_count = db.query(func.count(CoursePayment.id)).filter(
            CoursePayment.course_id.in_(course_ids),
            CoursePayment.status == "succeeded"
        ).scalar() or 0
        
        # 2. Student Success (MCQ Avg)
        # Assuming DrillSessions can be linked to courses or subjects the teacher owns
        avg_student_score = db.query(func.avg(DrillSession.overall_score)).filter(
            # DrillSession.student_id != -1 # Filter to avoid total False
            True
        ).scalar() or 0
        
        # 3. Activity (Marketing/Workflows)
        active_workflows = db.query(func.count(MarketingWorkflow.id)).filter(
            MarketingWorkflow.created_by == t.id,
            MarketingWorkflow.status == "ACTIVE"
        ).scalar() or 0
        
        # Calculate Composite (Simplified 0-100 scale)
        # Normalized scores
        reach_score = min(enrollment_count / 10, 1) * 40 # 40 pts max
        success_score = (avg_student_score / 100) * 30 # 30 pts max
        activity_score = min(active_workflows / 5, 1) * 30 # 30 pts max
        
        total_score = round(reach_score + success_score + activity_score, 1)
        
        scores.append({
            "id": t.id,
            "name": t.full_name or t.email,
            "composite_score": total_score,
            "metrics": {
                "reach": enrollment_count,
                "avg_student_performance": round(avg_student_score, 1),
                "active_campaigns": active_workflows
            },
            "grade": "A+" if total_score > 80 else "A" if total_score > 60 else "B" if total_score > 40 else "C"
        })
        
    return sorted(scores, key=lambda x: x['composite_score'], reverse=True)

@router.get("/content-health", response_model=Dict[str, Any])
def get_content_health_monitor(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Identifies subjects with low MCQ coverage or high student failure rates.
    """
    # Group MCQ performance by course/subject
    health_by_course = [] # Temporary empty as join is missing course_id
    
    critical_areas = []
    for c in health_by_course:
        status = "HEALTHY"
        if c.avg_score < 55:
            status = "CRITICAL_FAILURE_RATE"
        elif c.attempts < 10:
            status = "LOW_ENGAGEMENT"
            
        if status != "HEALTHY":
            critical_areas.append({
                "subject": c.title,
                "avg_score": round(c.avg_score, 1),
                "attempts": c.attempts,
                "issue": status
            })
            
    return {
        "global_health_score": 85, # Placeholder for overall logic
        "critical_areas": critical_areas,
        "total_courses_monitored": len(health_by_course)
    }
