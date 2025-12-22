"""
Permission and role-based access control (RBAC) dependencies.
Used as FastAPI dependencies to protect endpoints.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import permissions as crud_permissions
from app.models.user import User
from app.models.course import Course
from app.models.learning_path import LearningPath


def require_permission(permission_name: str):
    """
    Dependency factory that creates a permission check dependency.

    Usage:
        @router.post("/courses/", dependencies=[Depends(require_permission("create_course"))])

    Args:
        permission_name: Name of the required permission (e.g., "create_course")

    Returns:
        Dependency function that checks if current user has the permission
    """

    async def permission_checker(
        current_user: User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db),
    ) -> User:
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        # Check if user has the required permission
        has_permission = crud_permissions.check_permission(
            db=db, user_id=current_user.id, permission_name=permission_name
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_name} required",
            )

        return current_user

    return permission_checker


def require_role(role_name: str):
    """
    Dependency factory that creates a role check dependency.

    Usage:
        @router.post("/admin/...", dependencies=[Depends(require_role("admin"))])

    Args:
        role_name: Name of the required role (e.g., "admin", "instructor")

    Returns:
        Dependency function that checks if current user has the role
    """

    async def role_checker(
        current_user: User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db),
    ) -> User:
        # Superusers bypass all role checks
        if current_user.is_superuser:
            return current_user

        # Check if user has the required role
        has_role = crud_permissions.check_role(
            db=db, user_id=current_user.id, role_name=role_name
        )

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}",
            )

        return current_user

    return role_checker


def is_course_instructor(course_id: int):
    """
    Dependency factory that checks if current user is the instructor of a specific course.

    Usage:
        @router.put("/courses/{course_id}", dependencies=[Depends(is_course_instructor)])

    Args:
        course_id: ID of the course to check

    Returns:
        Dependency function that checks if current user is the course instructor
    """

    async def instructor_checker(
        current_user: User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db),
    ) -> User:
        # Superusers bypass check
        if current_user.is_superuser:
            return current_user

        # Get course
        course = db.query(Course).filter(Course.id == course_id).first()

        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
            )

        # Check if user is the instructor
        if course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the course instructor can perform this action",
            )

        return current_user

    return instructor_checker


def is_learning_path_creator(path_id: int):
    """
    Dependency factory that checks if current user is the creator of a specific learning path.

    Usage:
        @router.put("/learning-paths/{path_id}", dependencies=[Depends(is_learning_path_creator)])

    Args:
        path_id: ID of the learning path to check

    Returns:
        Dependency function that checks if current user is the path creator
    """

    async def creator_checker(
        current_user: User = Depends(deps.get_current_active_user),
        db: Session = Depends(deps.get_db),
    ) -> User:
        # Superusers bypass check
        if current_user.is_superuser:
            return current_user

        # Get learning path
        path = db.query(LearningPath).filter(LearningPath.id == path_id).first()

        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found"
            )

        # Check if user is the creator
        if path.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the learning path creator can perform this action",
            )

        return current_user

    return creator_checker


def require_instructor_role(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> User:
    """
    Simple dependency that requires the user to have the instructor role.

    Usage:
        @router.post("/courses/", dependencies=[Depends(require_instructor_role)])
    """
    if current_user.is_superuser:
        return current_user

    has_role = crud_permissions.check_role(
        db=db, user_id=current_user.id, role_name="instructor"
    )

    if not has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Instructor role required"
        )

    return current_user


def require_admin_role(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> User:
    """
    Simple dependency that requires the user to have the admin role.

    Usage:
        @router.delete("/users/{user_id}", dependencies=[Depends(require_admin_role)])
    """
    if current_user.is_superuser:
        return current_user

    has_role = crud_permissions.check_role(
        db=db, user_id=current_user.id, role_name="admin"
    )

    if not has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )

    return current_user


def require_student_role(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> User:
    """
    Simple dependency that requires the user to have the student role.
    Most endpoints don't need this as students are the default role.

    Usage:
        @router.post("/courses/{course_id}/enroll", dependencies=[Depends(require_student_role)])
    """
    if current_user.is_superuser:
        return current_user

    has_role = crud_permissions.check_role(
        db=db, user_id=current_user.id, role_name="student"
    )

    if not has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student role required"
        )

    return current_user
