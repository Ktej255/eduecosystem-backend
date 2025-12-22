"""Advanced User Management API endpoints."""
from typing import Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app import models
from app.api import deps
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.user_management import DataMaskingConfig, UserPermission, UserSession
from app.schemas.user_management import (
    DataMaskingConfig as DataMaskingConfigSchema,
    DataMaskingConfigCreate,
    DataMaskingConfigUpdate,
    UserPermission as UserPermissionSchema,
    UserPermissionCreate,
    UserPermissionUpdate,
    UserSession as UserSessionSchema,
    ActivityLog as ActivityLogSchema,
    UserWithPermissions,
    UserManagementStats,
)

router = APIRouter()


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/users", response_model=List[UserWithPermissions])
def get_managed_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get list of users with their permissions for management."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) | 
            (User.full_name.ilike(search_filter))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Count active sessions
        active_sessions = db.query(UserSession).filter(
            and_(UserSession.user_id == user.id, UserSession.is_active == True)
        ).count()
        
        # Get permissions
        permissions = db.query(UserPermission).filter(UserPermission.user_id == user.id).first()
        
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_banned": user.is_banned,
            "last_login": user.last_login,
            "permissions": permissions,
            "active_sessions": active_sessions,
        })
    
    return result


@router.get("/stats", response_model=UserManagementStats)
def get_user_management_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get user management dashboard statistics."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    banned_users = db.query(User).filter(User.is_banned == True).count()
    
    # Users by role
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role: count for role, count in role_counts}
    
    # Active sessions
    active_sessions = db.query(UserSession).filter(UserSession.is_active == True).count()
    
    # Recent activities (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_activities = db.query(ActivityLog).filter(
        ActivityLog.timestamp >= yesterday
    ).order_by(ActivityLog.timestamp.desc()).limit(50).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "users_by_role": users_by_role,
        "active_sessions": active_sessions,
        "recent_activities": recent_activities,
    }


@router.post("/users/{user_id}/ban")
def ban_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Ban a user and terminate all their sessions."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    
    user.is_banned = True
    user.is_active = False
    
    # Terminate all sessions
    db.query(UserSession).filter(UserSession.user_id == user_id).update(
        {"is_active": False, "logout_at": datetime.utcnow()}
    )
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="USER_BANNED",
        details=f"Banned user {user.email} (ID: {user_id})"
    )
    db.add(log)
    
    db.commit()
    return {"message": f"User {user.email} has been banned"}


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Unban a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_banned = False
    user.is_active = True
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="USER_UNBANNED",
        details=f"Unbanned user {user.email} (ID: {user_id})"
    )
    db.add(log)
    
    db.commit()
    return {"message": f"User {user.email} has been unbanned"}


# ============================================================================
# PERMISSIONS
# ============================================================================

@router.get("/permissions/{user_id}", response_model=UserPermissionSchema)
def get_user_permissions(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get permissions for a specific user."""
    permissions = db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
    
    if not permissions:
        # Return default permissions
        return UserPermissionSchema(
            id=0,
            user_id=user_id,
            created_at=datetime.utcnow(),
        )
    
    return permissions


@router.put("/permissions/{user_id}", response_model=UserPermissionSchema)
def update_user_permissions(
    user_id: int,
    permissions_in: UserPermissionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Update permissions for a user."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get or create permissions
    permissions = db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
    
    if not permissions:
        permissions = UserPermission(user_id=user_id, **permissions_in.dict())
        db.add(permissions)
    else:
        update_data = permissions_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permissions, field, value)
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="PERMISSIONS_UPDATED",
        details=f"Updated permissions for user {user.email} (ID: {user_id})"
    )
    db.add(log)
    
    db.commit()
    db.refresh(permissions)
    return permissions


# ============================================================================
# DATA MASKING
# ============================================================================

@router.get("/data-masking", response_model=List[DataMaskingConfigSchema])
def get_data_masking_configs(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get all data masking configurations."""
    configs = db.query(DataMaskingConfig).all()
    return configs


@router.post("/data-masking", response_model=DataMaskingConfigSchema)
def create_data_masking_config(
    config_in: DataMaskingConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Create a new data masking configuration."""
    config = DataMaskingConfig(**config_in.dict())
    db.add(config)
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="DATA_MASKING_CREATED",
        details=f"Created data masking config for role={config_in.role}, user_id={config_in.user_id}"
    )
    db.add(log)
    
    db.commit()
    db.refresh(config)
    return config


@router.put("/data-masking/{config_id}", response_model=DataMaskingConfigSchema)
def update_data_masking_config(
    config_id: int,
    config_in: DataMaskingConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Update a data masking configuration."""
    config = db.query(DataMaskingConfig).filter(DataMaskingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    update_data = config_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/data-masking/{config_id}")
def delete_data_masking_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Delete a data masking configuration."""
    config = db.query(DataMaskingConfig).filter(DataMaskingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    db.delete(config)
    db.commit()
    return {"message": "Data masking config deleted"}


# ============================================================================
# ACTIVITY LOGS
# ============================================================================

@router.get("/activity-logs", response_model=List[ActivityLogSchema])
def get_activity_logs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get activity logs with filtering."""
    query = db.query(ActivityLog)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if action:
        query = query.filter(ActivityLog.action.ilike(f"%{action}%"))
    
    if date_from:
        query = query.filter(ActivityLog.timestamp >= date_from)
    
    if date_to:
        query = query.filter(ActivityLog.timestamp <= date_to)
    
    logs = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs


# ============================================================================
# SESSIONS
# ============================================================================

@router.get("/sessions", response_model=List[UserSessionSchema])
def get_all_sessions(
    db: Session = Depends(deps.get_db),
    active_only: bool = True,
    user_id: Optional[int] = None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Get all user sessions."""
    query = db.query(UserSession)
    
    if active_only:
        query = query.filter(UserSession.is_active == True)
    
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
    
    sessions = query.order_by(UserSession.login_at.desc()).all()
    return sessions


@router.post("/sessions/{session_id}/terminate")
def terminate_session(
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Terminate a specific user session."""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.logout_at = datetime.utcnow()
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="SESSION_TERMINATED",
        details=f"Terminated session {session_id} for user ID {session.user_id}"
    )
    db.add(log)
    
    db.commit()
    return {"message": "Session terminated"}


@router.post("/sessions/terminate-all/{user_id}")
def terminate_all_sessions(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Terminate all sessions for a specific user."""
    count = db.query(UserSession).filter(
        and_(UserSession.user_id == user_id, UserSession.is_active == True)
    ).update({"is_active": False, "logout_at": datetime.utcnow()})
    
    # Log the action
    log = ActivityLog(
        user_id=current_user.id,
        action="ALL_SESSIONS_TERMINATED",
        details=f"Terminated {count} sessions for user ID {user_id}"
    )
    db.add(log)
    
    db.commit()
    return {"message": f"Terminated {count} sessions for user {user_id}"}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def mask_value(value: str, pattern: str = "partial") -> str:
    """Mask a value based on the pattern."""
    if not value:
        return value
    
    if pattern == "full":
        return "****"
    elif pattern == "hash":
        return f"#{hash(value) % 10000:04d}"
    else:  # partial
        if "@" in value:  # Email
            parts = value.split("@")
            if len(parts[0]) > 2:
                return f"{parts[0][:2]}***@{parts[1]}"
            return f"***@{parts[1]}"
        elif len(value) > 4:  # Phone or other
            return f"{value[:2]}****{value[-2:]}"
        else:
            return "****"


def should_mask_for_user(db: Session, user: User, field: str) -> bool:
    """Check if a field should be masked for the given user."""
    # Superusers see everything
    if user.is_superuser:
        return False
    
    # Check user-specific config first
    config = db.query(DataMaskingConfig).filter(
        and_(DataMaskingConfig.user_id == user.id, DataMaskingConfig.is_active == True)
    ).first()
    
    # Then check role-based config
    if not config:
        config = db.query(DataMaskingConfig).filter(
            and_(DataMaskingConfig.role == user.role, DataMaskingConfig.is_active == True)
        ).first()
    
    if not config:
        return False
    
    field_mapping = {
        "email": config.mask_email,
        "phone": config.mask_phone,
        "address": config.mask_address,
        "financial": config.mask_financial,
    }
    
    if field in field_mapping:
        return field_mapping[field]
    
    # Check custom fields
    if config.custom_masked_fields and field in config.custom_masked_fields:
        return True
    
    return False
