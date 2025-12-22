"""
CRUD operations for Permissions and Roles.
Handles role-based access control (RBAC) operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.permissions import Role, Permission
from app.models.user import User
from app.schemas.permissions import RoleCreate, RoleUpdate, PermissionCreate


# ==================== Permission CRUD ====================


def create_permission(db: Session, permission: PermissionCreate) -> Permission:
    """Create a new permission"""
    db_permission = Permission(**permission.model_dump())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
    """Get permission by ID"""
    return db.query(Permission).filter(Permission.id == permission_id).first()


def get_permission_by_name(db: Session, name: str) -> Optional[Permission]:
    """Get permission by name"""
    return db.query(Permission).filter(Permission.name == name).first()


def get_permissions(
    db: Session, skip: int = 0, limit: int = 100, resource: Optional[str] = None
) -> List[Permission]:
    """Get list of permissions with optional filtering"""
    query = db.query(Permission)

    if resource:
        query = query.filter(Permission.resource == resource)

    return query.offset(skip).limit(limit).all()


def get_permissions_count(db: Session, resource: Optional[str] = None) -> int:
    """Get total count of permissions"""
    query = db.query(Permission)

    if resource:
        query = query.filter(Permission.resource == resource)

    return query.count()


# ==================== Role CRUD ====================


def create_role(db: Session, role: RoleCreate) -> Role:
    """Create a new role with permissions"""
    # Create role
    role_data = role.model_dump(exclude={"permission_ids"})
    db_role = Role(**role_data)

    # Add permissions if provided
    if role.permission_ids:
        permissions = (
            db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        )
        db_role.permissions = permissions

    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def get_role(db: Session, role_id: int) -> Optional[Role]:
    """Get role by ID with permissions"""
    return (
        db.query(Role)
        .options(joinedload(Role.permissions))
        .filter(Role.id == role_id)
        .first()
    )


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get role by name with permissions"""
    return (
        db.query(Role)
        .options(joinedload(Role.permissions))
        .filter(Role.name == name)
        .first()
    )


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """Get list of roles with permissions"""
    return (
        db.query(Role)
        .options(joinedload(Role.permissions))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_roles_count(db: Session) -> int:
    """Get total count of roles"""
    return db.query(Role).count()


def update_role(db: Session, role_id: int, role_update: RoleUpdate) -> Optional[Role]:
    """Update a role"""
    db_role = get_role(db, role_id)

    if not db_role:
        return None

    # Update basic fields
    update_data = role_update.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for field, value in update_data.items():
        setattr(db_role, field, value)

    # Update permissions if provided
    if role_update.permission_ids is not None:
        permissions = (
            db.query(Permission)
            .filter(Permission.id.in_(role_update.permission_ids))
            .all()
        )
        db_role.permissions = permissions

    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, role_id: int) -> bool:
    """Delete a role (only if not a system role)"""
    db_role = get_role(db, role_id)

    if not db_role:
        return False

    if db_role.is_system_role:
        raise ValueError("Cannot delete system roles")

    db.delete(db_role)
    db.commit()
    return True


# ==================== User-Role Assignment ====================


def assign_role_to_user(db: Session, user_id: int, role_id: int) -> bool:
    """Assign a role to a user"""
    user = db.query(User).filter(User.id == user_id).first()
    role = get_role(db, role_id)

    if not user or not role:
        return False

    # Check if user already has this role
    if role in user.roles:
        return True

    user.roles.append(role)
    db.commit()
    return True


def assign_role_to_user_by_name(db: Session, user_id: int, role_name: str) -> bool:
    """Assign a role to a user by role name"""
    role = get_role_by_name(db, role_name)

    if not role:
        return False

    return assign_role_to_user(db, user_id, role.id)


def remove_role_from_user(db: Session, user_id: int, role_id: int) -> bool:
    """Remove a role from a user"""
    user = (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user_id)
        .first()
    )
    role = get_role(db, role_id)

    if not user or not role:
        return False

    if role in user.roles:
        user.roles.remove(role)
        db.commit()
        return True

    return False


def get_user_roles(db: Session, user_id: int) -> List[Role]:
    """Get all roles assigned to a user"""
    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(Role.permissions))
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return []

    return user.roles


def get_user_permissions(db: Session, user_id: int) -> List[Permission]:
    """Get all permissions for a user (from all assigned roles)"""
    roles = get_user_roles(db, user_id)

    # Aggregate all permissions from all roles (remove duplicates)
    permissions = []
    seen_permission_ids = set()

    for role in roles:
        for permission in role.permissions:
            if permission.id not in seen_permission_ids:
                permissions.append(permission)
                seen_permission_ids.add(permission.id)

    return permissions


def check_permission(db: Session, user_id: int, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.
    Returns True if user has the permission through any of their roles.
    """
    permissions = get_user_permissions(db, user_id)
    return any(p.name == permission_name for p in permissions)


def check_role(db: Session, user_id: int, role_name: str) -> bool:
    """
    Check if a user has a specific role.
    Returns True if user has the role assigned.
    """
    roles = get_user_roles(db, user_id)
    return any(r.name == role_name for r in roles)


def get_users_with_role(
    db: Session, role_id: int, skip: int = 0, limit: int = 100
) -> List[User]:
    """Get all users with a specific role"""
    role = get_role(db, role_id)

    if not role:
        return []

    return (
        db.query(User)
        .join(User.roles)
        .filter(Role.id == role_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_users_with_permission(
    db: Session, permission_name: str, skip: int = 0, limit: int = 100
) -> List[User]:
    """Get all users who have a specific permission (through any role)"""
    permission = get_permission_by_name(db, permission_name)

    if not permission:
        return []

    # Get all roles that have this permission
    roles_with_permission = (
        db.query(Role)
        .join(Role.permissions)
        .filter(Permission.id == permission.id)
        .all()
    )

    if not roles_with_permission:
        return []

    # Get all users with any of these roles
    role_ids = [r.id for r in roles_with_permission]

    return (
        db.query(User)
        .join(User.roles)
        .filter(Role.id.in_(role_ids))
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )
