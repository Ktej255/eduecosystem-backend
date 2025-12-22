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
