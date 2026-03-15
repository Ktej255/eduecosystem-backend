from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.api.api_v1.endpoints.admin_teacher_performance import get_teacher_performance

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def list_teachers(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get a list of all teachers with their basic performance summary.
    """
    teachers = db.query(User).filter(User.role.in_(["teacher", "admin"])).all()
    
    results = []
    for t in teachers:
        # Get course count
        course_count = db.query(Course).filter(Course.instructor_id == t.id).count()
        
        # Get performance summary (reusing existing logic)
        try:
            perf = get_teacher_performance(t.id, db, current_admin)
            score = perf.get("composite_score", 0)
            grade = perf.get("grade", "N/A")
        except:
            score = 0
            grade = "N/A"
            
        results.append({
            "id": t.id,
            "full_name": t.full_name,
            "email": t.email,
            "role": t.role,
            "course_count": course_count,
            "composite_score": score,
            "grade": grade,
            "is_active": t.is_active,
            "last_login": t.last_login
        })
        
    return results

@router.get("/summary", response_model=Dict[str, Any])
def get_teacher_management_summary(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    High-level stats for the teacher management dashboard.
    """
    total_teachers = db.query(User).filter(User.role.in_(["teacher", "admin"])).count()
    active_now = 0 # Placeholder for real-time
    
    # Average score
    # (Simple average for now)
    teachers = db.query(User).filter(User.role.in_(["teacher", "admin"])).all()
    total_score = 0
    count = 0
    for t in teachers:
        try:
            perf = get_teacher_performance(t.id, db, current_admin)
            total_score += perf.get("composite_score", 0)
            count += 1
        except:
            pass
            
    avg_score = (total_score / count) if count > 0 else 0
    
    return {
        "total_teachers": total_teachers,
        "active_teachers": total_teachers, # Assume all for now
        "average_performance_score": round(avg_score, 1),
        "top_performer": "No data" if count == 0 else "Analysis Pending"
    }
