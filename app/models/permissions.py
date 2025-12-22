from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


class Role(Base):
    """
    Role model for RBAC system.
    Predefined roles: admin, instructor, student, moderator
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_system_role = Column(
        Boolean, default=False, nullable=False
    )  # Cannot be deleted if True
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", secondary=user_roles, back_populates="roles")


class Permission(Base):
    """
    Permission model for granular access control.
    Examples: create_course, edit_course, delete_course, grade_assignment, etc.
    """

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(String(500))
    resource = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'course', 'assignment', 'user'
    action = Column(
        String(50), nullable=False, index=True
    )  # e.g., 'create', 'read', 'update', 'delete'
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )
