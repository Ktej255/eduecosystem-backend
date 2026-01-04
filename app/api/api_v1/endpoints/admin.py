from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from app.api import deps
from app.models.user import User
from app.models.submission import HandwritingSubmission
from app.models.shadow_mode import ShadowModeSession
from app.models.group import Group
from app.models.admin_log import AdminLog
from app.crud import user as crud_user
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Get platform-wide statistics for admin dashboard.
    """
    # User statistics
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    banned_users = db.query(func.count(User.id)).filter(User.is_banned == True).scalar()

    # Recent signups (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    # Note: Assuming created_at exists or using id as proxy
    new_users_week = total_users  # Placeholder

    # Content statistics
    total_submissions = db.query(func.count(HandwritingSubmission.id)).scalar()
    total_sessions = db.query(func.count(ShadowModeSession.id)).scalar()
    total_groups = db.query(func.count(Group.id)).scalar()

    # Engagement
    avg_coins = db.query(func.avg(User.coins)).scalar() or 0
    avg_streak = db.query(func.avg(User.streak_days)).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "banned": banned_users,
            "new_this_week": new_users_week,
        },
        "content": {
            "submissions": total_submissions,
            "shadow_sessions": total_sessions,
            "groups": total_groups,
        },
        "engagement": {
            "avg_coins": round(avg_coins, 2),
            "avg_streak": round(avg_streak, 2),
        },
    }


@router.get("/users")
def list_all_users(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_banned: Optional[bool] = Query(None),
) -> Any:
    """
    Get list of all users with filters.
    """
    query = db.query(User)

    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )

    if role:
        query = query.filter(User.role == role)

    if is_banned is not None:
        query = query.filter(User.is_banned == is_banned)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return {"total": total, "users": jsonable_encoder(users)}


@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Get detailed information about a specific user.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user statistics
    submissions_count = (
        db.query(func.count(HandwritingSubmission.id))
        .filter(HandwritingSubmission.user_id == user_id)
        .scalar()
    )

    sessions_count = (
        db.query(func.count(ShadowModeSession.id))
        .filter(ShadowModeSession.user_id == user_id)
        .scalar()
    )

    return {
        "user": jsonable_encoder(user),
        "statistics": {
            "submissions": submissions_count,
            "shadow_sessions": sessions_count,
        },
    }


@router.put("/users/{user_id}/ban")
def ban_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Ban a user from the platform.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = True
    user.is_active = False
    db.commit()

    # Log admin action
    log = AdminLog(
        admin_id=current_admin.id,
        action="ban_user",
        target_type="user",
        target_id=user_id,
        details=f"Banned user {user.email}",
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return {"message": "User banned successfully", "user": jsonable_encoder(user)}


@router.put("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Unban a user.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = False
    user.is_active = True
    db.commit()

    # Log admin action
    log = AdminLog(
        admin_id=current_admin.id,
        action="unban_user",
        target_type="user",
        target_id=user_id,
        details=f"Unbanned user {user.email}",
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return {"message": "User unbanned successfully", "user": jsonable_encoder(user)}


@router.put("/users/{user_id}/promote")
def promote_to_admin(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Promote a user to admin.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = "admin"
    db.commit()

    # Log admin action
    log = AdminLog(
        admin_id=current_admin.id,
        action="promote_user",
        target_type="user",
        target_id=user_id,
        details=f"Promoted {user.email} to admin",
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return {"message": "User promoted to admin", "user": jsonable_encoder(user)}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Delete a user (soft delete by marking inactive).
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin users")

    user.is_active = False
    db.commit()

    # Log admin action
    log = AdminLog(
        admin_id=current_admin.id,
        action="delete_user",
        target_type="user",
        target_id=user_id,
        details=f"Deleted user {user.email}",
    )
    db.add(log)
    db.commit()

    return {"message": "User deleted successfully"}


@router.get("/logs")
def get_admin_logs(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get recent admin activity logs.
    """
    logs = (
        db.query(AdminLog)
        .order_by(desc(AdminLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"logs": jsonable_encoder(logs)}


@router.get("/overview")
def get_admin_overview(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Get comprehensive overview for admin dashboard.
    Includes student stats, batch authorizations, test completions, and activity.
    """
    from app.models.batch1 import Batch1TestResult
    from app.models.study_session import StudySession
    
    # User counts
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_teachers = db.query(func.count(User.id)).filter(User.role.in_(["teacher", "admin"])).scalar() or 0
    
    # Batch authorizations
    batch1_count = db.query(func.count(User.id)).filter(User.is_batch1_authorized == True).scalar() or 0
    ras_count = db.query(func.count(User.id)).filter(User.is_ras_authorized == True).scalar() or 0
    
    # Test activity
    total_tests = db.query(func.count(Batch1TestResult.id)).scalar() or 0
    avg_score = db.query(func.avg(Batch1TestResult.score)).scalar() or 0
    
    # Study sessions (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_study_sessions = db.query(func.count(StudySession.id)).filter(
        StudySession.start_time >= week_ago
    ).scalar() or 0
    
    # Active users (logged in last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    active_today = db.query(func.count(User.id)).filter(
        User.last_login >= day_ago
    ).scalar() or 0
    
    return {
        "users": {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "active_today": active_today,
        },
        "batches": {
            "batch1_authorized": batch1_count,
            "ras_authorized": ras_count,
        },
        "activity": {
            "total_tests_taken": total_tests,
            "average_score": round(avg_score, 2) if avg_score else 0,
            "study_sessions_this_week": recent_study_sessions,
        }
    }


@router.get("/teachers")
def get_all_teachers(
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get all teachers with their student counts and upload statistics.
    """
    teachers = db.query(User).filter(
        User.role.in_(["teacher", "admin"])
    ).offset(skip).limit(limit).all()
    
    teacher_data = []
    for teacher in teachers:
        # Count students (all students for now, can be filtered by assignment later)
        student_count = db.query(func.count(User.id)).filter(
            User.role == "student"
        ).scalar() or 0
        
        teacher_data.append({
            "id": teacher.id,
            "email": teacher.email,
            "full_name": teacher.full_name,
            "role": teacher.role,
            "last_login": teacher.last_login.isoformat() if teacher.last_login else None,
            "is_active": teacher.is_active,
            "student_count": student_count,
        })
    
    return {"teachers": teacher_data, "total": len(teacher_data)}


@router.get("/teachers/{teacher_id}/students")
def get_teacher_students(
    teacher_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get students under a specific teacher.
    """
    # Verify teacher exists
    teacher = crud_user.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Get all students (can be filtered by group/assignment later)
    students = db.query(User).filter(User.role == "student").offset(skip).limit(limit).all()
    
    return {
        "teacher": jsonable_encoder(teacher),
        "students": jsonable_encoder(students),
        "total": len(students)
    }


@router.get("/students/{student_id}/performance")
def get_student_performance(
    student_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Get comprehensive performance data for a specific student.
    Includes test history, study sessions, and progress metrics.
    """
    from app.models.batch1 import Batch1TestResult
    from app.models.study_session import StudySession
    
    student = crud_user.get(db, id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get test results
    test_results = db.query(Batch1TestResult).filter(
        Batch1TestResult.user_id == student_id
    ).order_by(desc(Batch1TestResult.timestamp)).limit(20).all()
    
    # Get study sessions
    study_sessions = db.query(StudySession).filter(
        StudySession.user_id == student_id
    ).order_by(desc(StudySession.start_time)).limit(20).all()
    
    # Calculate stats
    test_count = len(test_results)
    avg_score = sum(t.score for t in test_results) / test_count if test_count > 0 else 0
    best_score = max((t.score for t in test_results), default=0)
    total_study_time = sum(s.duration_seconds or 0 for s in study_sessions)
    
    return {
        "student": jsonable_encoder(student),
        "test_results": jsonable_encoder(test_results),
        "study_sessions": jsonable_encoder(study_sessions),
        "stats": {
            "total_tests": test_count,
            "average_score": round(avg_score, 2),
            "best_score": best_score,
            "total_study_time_minutes": round(total_study_time / 60, 1),
            "streak_days": student.streak_days,
            "coins_earned": student.coins,
        }
    }

@router.put("/users/{user_id}/access")
def update_user_batch_access(
    user_id: int,
    batch1: Optional[bool] = Query(None),
    batch2: Optional[bool] = Query(None),
    ras: Optional[bool] = Query(None),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Update user batch access permissions.
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if batch1 is not None:
        user.is_batch1_authorized = batch1
    if batch2 is not None:
        user.is_batch2_authorized = batch2
    if ras is not None:
        user.is_ras_authorized = ras
        
    db.commit()
    db.refresh(user)

    # Log action
    log = AdminLog(
        admin_id=current_admin.id,
        action="update_access",
        target_type="user",
        target_id=user_id,
        details=f"Updated access for {user.email}: Batch1={user.is_batch1_authorized}, Batch2={user.is_batch2_authorized}, RAS={user.is_ras_authorized}",
    )
    db.add(log)
    db.commit()

    return {"message": "User access updated successfully", "user": jsonable_encoder(user)}
