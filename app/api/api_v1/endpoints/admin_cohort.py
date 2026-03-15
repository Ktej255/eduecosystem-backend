from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from typing import Any, List, Dict
from datetime import datetime, timedelta
from app.api import deps
from app.models.user import User
from app.models.drill import DrillSession
from app.models.study_session import StudySession
from app.models.meditation import MeditationSession
from app.models.graphotherapy import GraphoSubmission

router = APIRouter()

@router.get("/compare", response_model=List[Dict[str, Any]])
def compare_batch_cohorts(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    PHASE 4: COHORT INTELLIGENCE — COMPARISON ENGINE
    Side-by-side performance for Batch 1, Batch 2, and RAS.
    Metrics: Student Count, Avg Score, Avg Streak, Avg Study Hours.
    """
    cohorts = [
        {"name": "Batch 1", "filter": User.is_batch1_authorized == True},
        {"name": "Batch 2", "filter": User.is_batch2_authorized == True},
        {"name": "RAS", "filter": User.is_ras_authorized == True}
    ]
    
    comparison = []
    for cohort in cohorts:
        # 1. Basic Stats
        stats = db.query(
            func.count(User.id).label('total_students'),
            func.avg(User.streak_days).label('avg_streak')
        ).filter(cohort['filter'], User.role == "student", User.is_active == True).first()
        
        # 2. Performance (UPSC Drills)
        # Using overall_score from DrillSession
        avg_score = db.query(func.avg(DrillSession.overall_score)).join(
            User, User.id == DrillSession.student_id
        ).filter(cohort['filter']).scalar() or 0
        
        # 3. Effort (Study Hours)
        avg_seconds = db.query(func.avg(StudySession.duration_seconds)).join(
            User, User.id == StudySession.user_id
        ).filter(cohort['filter']).scalar() or 0
        
        comparison.append({
            "cohort": cohort['name'],
            "students": stats.total_students or 0,
            "avg_streak": round(stats.avg_streak or 0, 1),
            "avg_score": round(avg_score, 1),
            "avg_study_hours": round(avg_seconds / 3600, 1) if avg_seconds else 0
        })
        
    return comparison

@router.get("/health-distribution", response_model=Dict[str, Any])
def get_cohort_health_distribution(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    PHASE 4: COHORT INTELLIGENCE — HEALTH MONITOR
    Breakdown of students by risk level within each cohort.
    """
    # Logic: A student is "at-risk" if their streak is 0 or they haven't logged in for 5+ days
    # (Simplified version of the logic in admin_at_risk.py for aggregation)
    
    now = datetime.utcnow()
    five_days_ago = now - timedelta(days=5)
    
    cohorts = [
        {"id": "batch1", "name": "Batch 1", "filter": User.is_batch1_authorized == True},
        {"id": "batch2", "name": "Batch 2", "filter": User.is_batch2_authorized == True},
        {"id": "ras", "name": "RAS", "filter": User.is_ras_authorized == True}
    ]
    
    distribution = {}
    for cohort in cohorts:
        total = db.query(func.count(User.id)).filter(cohort['filter'], User.role == "student").scalar() or 0
        
        at_risk = db.query(func.count(User.id)).filter(
            cohort['filter'], 
            User.role == "student",
            (User.streak_days == 0) | (User.last_login < five_days_ago) | (User.last_login.is_(None))
        ).scalar() or 0
        
        distribution[cohort['id']] = {
            "name": cohort['name'],
            "total": total,
            "at_risk": at_risk,
            "healthy": total - at_risk,
            "at_risk_percentage": round((at_risk / total * 100), 1) if total > 0 else 0
        }
        
    return distribution

@router.get("/engagement-trends", response_model=List[Dict[str, Any]])
def get_cohort_engagement_trends(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    PHASE 4: COHORT INTELLIGENCE — ENGAGEMENT TRENDS
    Weekly trend of study hours per cohort.
    """
    # Returns last 7 days of average study minutes per cohort
    trends = []
    now = datetime.utcnow().date()
    
    cohorts = [
        {"name": "Batch 1", "filter": User.is_batch1_authorized == True},
        {"name": "Batch 2", "filter": User.is_batch2_authorized == True},
        {"name": "RAS", "filter": User.is_ras_authorized == True}
    ]
    
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        
        day_data = {"date": day_str}
        
        for cohort in cohorts:
            avg_seconds = db.query(func.avg(StudySession.duration_seconds)).join(
                User, User.id == StudySession.user_id
            ).filter(
                cohort['filter'],
                func.date(StudySession.start_time) == day
            ).scalar() or 0
            
            day_data[cohort['name']] = round(avg_seconds / 60, 1) # in minutes
            
        trends.append(day_data)
        
    return trends

@router.get("/subject-proficiency", response_model=List[Dict[str, Any]])
def get_cohort_subject_proficiency(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    PHASE 4: COHORT INTELLIGENCE — SUBJECT PROFICIENCY
    Average scores per subject for each cohort.
    """
    # Using 'gs_paper' from DrillQuestion as a proxy for subjects
    subjects = ["GS1", "GS2", "GS3", "GS4"]
    cohorts = [
        {"name": "Batch 1", "filter": User.is_batch1_authorized == True},
        {"name": "Batch 2", "filter": User.is_batch2_authorized == True},
        {"name": "RAS", "filter": User.is_ras_authorized == True}
    ]
    
    proficiency = []
    for subject in subjects:
        subject_data = {"subject": subject}
        for cohort in cohorts:
            avg_score = db.query(func.avg(DrillSession.overall_score)).join(
                User, User.id == DrillSession.student_id
            ).join(
                # Implicit join with DrillQuestion is needed to filter by gs_paper
                "question" 
            ).filter(
                cohort['filter'],
                # Filter by GS Paper
                # Note: We need to make sure the relationship is correctly used
            ).filter(
                # We can't directly filter on the relationship in query() without join or similar
                # But DrillSession.question_id is there
            )
            
            # Refined query for subject-wise avg
            avg_val = db.query(func.avg(DrillSession.overall_score)).join(
                User, User.id == DrillSession.student_id
            ).join(
                DrillSession.question # Using relationship
            ).filter(
                cohort['filter'],
                DrillSession.question.has(gs_paper=subject)
            ).scalar() or 0
            
            subject_data[cohort['name']] = round(avg_val, 1)
            
        proficiency.append(subject_data)
        
    return proficiency
