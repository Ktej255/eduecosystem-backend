"""
Admin Analytics API Endpoints
Provides analytics, insights, and reporting for admin portal
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.admin_analytics_service import admin_analytics_service

router = APIRouter()


def check_admin(current_user: User):
    """Verify user is admin"""
    if not current_user.is_superuser:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==================== INDIVIDUAL STUDENT ANALYTICS ====================

@router.get("/student/{student_id}/performance")
async def get_student_performance(
    student_id: UUID,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get individual student performance metrics"""
    return await admin_analytics_service.get_student_performance(
        db, student_id, start_date, end_date
    )


@router.get("/student/{student_id}/drill-history")
async def get_student_drill_history(
    student_id: UUID,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get student's drill history"""
    from app.models.drill import DrillSession
    
    sessions = db.query(DrillSession).filter(
        DrillSession.student_id == student_id,
        DrillSession.completed_at.isnot(None)
    ).order_by(DrillSession.date.desc()).limit(limit).all()
    
    return {
        "student_id": str(student_id),
        "total_sessions": len(sessions),
        "sessions": [
            {
                "id": str(s.id),
                "date": str(s.date),
                "question_number": s.question_number,
                "before_score": s.before_score,
                "after_score": s.after_score,
                "improvement": s.improvement,
                "overall_score": s.overall_score,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in sessions
        ]
    }


@router.get("/student/{student_id}/trends")
async def get_student_trends(
    student_id: UUID,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get student performance trends over time"""
    from app.models.drill import DrillSession
    from sqlalchemy import func, and_
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    daily_stats = db.query(
        DrillSession.date,
        func.avg(DrillSession.overall_score).label('avg_score'),
        func.avg(DrillSession.improvement).label('avg_improvement'),
        func.count(DrillSession.id).label('total_drills')
    ).filter(
        and_(
            DrillSession.student_id == student_id,
            DrillSession.date >= start_date,
            DrillSession.completed_at.isnot(None)
        )
    ).group_by(DrillSession.date).order_by(DrillSession.date).all()
    
    return {
        "student_id": str(student_id),
        "period": f"{start_date} to {end_date}",
        "trends": [
            {
                "date": str(stat.date),
                "average_score": round(stat.avg_score or 0, 2),
                "average_improvement": round(stat.avg_improvement or 0, 2),
                "total_drills": stat.total_drills
            }
            for stat in daily_stats
        ]
    }


# ==================== AGGREGATE ANALYTICS ====================

@router.get("/all-students/summary")
async def get_all_students_summary(
    gs_paper: Optional[str] = Query(None, pattern="^GS[1-4]$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get aggregate summary for all students"""
    return await admin_analytics_service.get_aggregate_analytics(
        db, gs_paper, start_date, end_date
    )


@router.get("/all-students/by-gs-paper")
async def get_performance_by_gs_paper(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get performance breakdown by GS paper"""
    results = {}
    
    for gs in ["GS1", "GS2", "GS3", "GS4"]:
        results[gs] = await admin_analytics_service.get_aggregate_analytics(db, gs)
    
    return results


@router.get("/all-students/by-topic")
async def get_performance_by_topic(
    gs_paper: Optional[str] = Query(None, pattern="^GS[1-4]$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get performance breakdown by topic"""
    return await admin_analytics_service.get_topic_performance(db, gs_paper)


# ==================== TRENDS & INSIGHTS ====================

@router.get("/trends/daily")
async def get_daily_trends(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get daily performance trends"""
    return await admin_analytics_service.get_daily_trends(db, days)


@router.get("/trends/weekly")
async def get_weekly_trends(
    weeks: int = Query(12, le=52),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get weekly performance trends"""
    from app.models.drill import DrillSession
    from sqlalchemy import func, and_, extract
    
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)
    
    weekly_stats = db.query(
        extract('year', DrillSession.date).label('year'),
        extract('week', DrillSession.date).label('week'),
        func.count(func.distinct(DrillSession.student_id)).label('total_students'),
        func.avg(DrillSession.overall_score).label('avg_score'),
        func.avg(DrillSession.improvement).label('avg_improvement')
    ).filter(
        and_(
            DrillSession.date >= start_date,
            DrillSession.completed_at.isnot(None)
        )
    ).group_by('year', 'week').order_by('year', 'week').all()
    
    return {
        "period": f"Last {weeks} weeks",
        "trends": [
            {
                "year": int(stat.year),
                "week": int(stat.week),
                "total_students": stat.total_students,
                "average_score": round(stat.avg_score or 0, 2),
                "average_improvement": round(stat.avg_improvement or 0, 2)
            }
            for stat in weekly_stats
        ]
    }


# ==================== AI INSIGHTS ====================

@router.post("/generate-insights")
async def generate_curriculum_insights(
    gs_paper: str = Query(..., pattern="^GS[1-4]$"),
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Generate AI-powered curriculum insights using Grok"""
    return await admin_analytics_service.generate_curriculum_insights(
        db, gs_paper, days
    )


@router.get("/curriculum-recommendations")
async def get_curriculum_recommendations(
    gs_paper: Optional[str] = Query(None, pattern="^GS[1-4]$"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Get recent curriculum recommendations"""
    from app.models.drill import CurriculumInsight
    
    query = db.query(CurriculumInsight)
    
    if gs_paper:
        query = query.filter(CurriculumInsight.gs_paper == gs_paper)
    
    insights = query.order_by(CurriculumInsight.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(insights),
        "insights": [
            {
                "id": str(i.id),
                "date": str(i.date),
                "gs_paper": i.gs_paper,
                "total_students": i.total_students,
                "average_score": i.average_score,
                "common_challenges": i.common_challenges,
                "high_performing_topics": i.high_performing_topics,
                "low_performing_topics": i.low_performing_topics,
                "ai_recommendations": i.ai_recommendations,
                "created_at": i.created_at.isoformat()
            }
            for i in insights
        ]
    }


# ==================== STUDENT LIST ====================

@router.get("/students/list")
async def list_all_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """List all students with drill statistics"""
    from app.models.drill import DrillSession
    from sqlalchemy import func
    
    # Get all students who have completed at least one drill
    student_stats = db.query(
        User.id,
        User.full_name,
        User.email,
        func.count(DrillSession.id).label('total_drills'),
        func.avg(DrillSession.overall_score).label('avg_score'),
        func.max(DrillSession.date).label('last_drill_date')
    ).join(
        DrillSession, User.id == DrillSession.student_id
    ).filter(
        DrillSession.completed_at.isnot(None)
    ).group_by(
        User.id, User.full_name, User.email
    ).offset(skip).limit(limit).all()
    
    return {
        "total": len(student_stats),
        "students": [
            {
                "id": str(s.id),
                "name": s.full_name,
                "email": s.email,
                "total_drills": s.total_drills,
                "average_score": round(s.avg_score or 0, 2),
                "last_drill_date": str(s.last_drill_date) if s.last_drill_date else None
            }
            for s in student_stats
        ]
    }
