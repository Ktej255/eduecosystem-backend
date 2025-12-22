from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


# Permission Schemas
class PermissionBase(BaseModel):
    """Base schema for Permission"""

    name: str = Field(
        ..., max_length=100, description="Unique permission name, e.g., 'create_course'"
    )
    display_name: str = Field(
        ..., max_length=200, description="Human-readable permission name"
    )
    description: Optional[str] = Field(None, max_length=500)
    resource: str = Field(
        ..., max_length=50, description="Resource type, e.g., 'course', 'assignment'"
    )
    action: str = Field(
        ...,
        max_length=50,
        description="Action type, e.g., 'create', 'read', 'update', 'delete'",
    )


class PermissionCreate(PermissionBase):
    """Schema for creating a new permission"""

    pass


class Permission(PermissionBase):
    """Schema for permission with ID and timestamps"""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Role Schemas
class RoleBase(BaseModel):
    """Base schema for Role"""

    name: str = Field(
        ..., max_length=50, description="Unique role name, e.g., 'admin', 'instructor'"
    )
    display_name: str = Field(
        ..., max_length=100, description="Human-readable role name"
    )
    description: Optional[str] = Field(None, max_length=500)
    is_system_role: bool = Field(
        default=False, description="System roles cannot be deleted"
    )


class RoleCreate(RoleBase):
    """Schema for creating a new role"""

    permission_ids: List[int] = Field(
        default=[], description="List of permission IDs to assign to this role"
    )


class RoleUpdate(BaseModel):
    """Schema for updating a role"""

    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: Optional[List[int]] = Field(
        None, description="Update permissions assigned to this role"
    )


class Role(RoleBase):
    """Schema for role with ID and timestamps"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(Role):
    """Schema for role including its permissions"""

    permissions: List[Permission] = []


# User Role Assignment Schemas
class UserRoleAssignment(BaseModel):
    """Schema for assigning a role to a user"""

    user_id: int
    role_id: int


class UserRoleAssignmentByName(BaseModel):
    """Schema for assigning a role to a user by role name"""

    user_id: int
    role_name: str = Field(
        ..., description="Role name, e.g., 'admin', 'instructor', 'student'"
    )


# User with Roles Schema
class UserWithRoles(BaseModel):
    """Schema for user including their roles"""

    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    is_active: bool
    roles: List[Role] = []

    model_config = ConfigDict(from_attributes=True)


# Permission Check Schemas
class PermissionCheckRequest(BaseModel):
    """Schema for checking if a user has a specific permission"""

    user_id: int
    permission_name: str


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response"""

    has_permission: bool
    user_id: int
    permission_name: str
    granted_by_roles: List[str] = Field(
        default=[], description="List of role names that grant this permission"
    )


# List Schemas
class RoleList(BaseModel):
    """Paginated list of roles"""

    items: List[RoleWithPermissions]
    total: int
    page: int = 1
    page_size: int = 50


class PermissionList(BaseModel):
    """Paginated list of permissions"""

    items: List[Permission]
    total: int
    page: int = 1
    page_size: int = 50
