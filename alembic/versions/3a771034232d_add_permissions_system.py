"""add_permissions_system

Revision ID: 3a771034232d
Revises: c1e3511d07a6
Create Date: 2025-11-24 08:08:58.546527

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a771034232d"
down_revision: Union[str, Sequence[str], None] = "c1e3511d07a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create permissions system tables and seed default data."""

    # Create roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)
    op.create_index(
        op.f("ix_permissions_resource"), "permissions", ["resource"], unique=False
    )
    op.create_index(
        op.f("ix_permissions_action"), "permissions", ["action"], unique=False
    )

    # Create role_permissions association table
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # Create user_roles association table
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # Seed default roles
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_system_role", sa.Boolean),
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "id": 1,
                "name": "admin",
                "display_name": "Administrator",
                "description": "Full system access with all permissions",
                "is_system_role": True,
            },
            {
                "id": 2,
                "name": "instructor",
                "display_name": "Instructor",
                "description": "Can create and manage courses, grade assignments",
                "is_system_role": True,
            },
            {
                "id": 3,
                "name": "student",
                "display_name": "Student",
                "description": "Can enroll in courses, submit assignments, take quizzes",
                "is_system_role": True,
            },
            {
                "id": 4,
                "name": "moderator",
                "display_name": "Moderator",
                "description": "Can moderate discussions and manage user content",
                "is_system_role": True,
            },
        ],
    )

    # Seed default permissions
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
    )

    permissions_data = [
        # Course permissions
        (1, "create_course", "Create Course", "Create new courses", "course", "create"),
        (2, "edit_course", "Edit Course", "Edit course details", "course", "update"),
        (3, "delete_course", "Delete Course", "Delete courses", "course", "delete"),
        (
            4,
            "publish_course",
            "Publish Course",
            "Publish courses to students",
            "course",
            "publish",
        ),
        (
            5,
            "view_all_courses",
            "View All Courses",
            "View all courses in system",
            "course",
            "read",
        ),
        # Assignment permissions
        (
            6,
            "create_assignment",
            "Create Assignment",
            "Create course assignments",
            "assignment",
            "create",
        ),
        (
            7,
            "grade_assignment",
            "Grade Assignment",
            "Grade student submissions",
            "assignment",
            "grade",
        ),
        (
            8,
            "delete_assignment",
            "Delete Assignment",
            "Delete assignments",
            "assignment",
            "delete",
        ),
        (
            9,
            "submit_assignment",
            "Submit Assignment",
            "Submit assignment solutions",
            "assignment",
            "submit",
        ),
        # Learning Path permissions
        (
            10,
            "create_learning_path",
            "Create Learning Path",
            "Create learning paths",
            "learning_path",
            "create",
        ),
        (
            11,
            "edit_learning_path",
            "Edit Learning Path",
            "Edit learning paths",
            "learning_path",
            "update",
        ),
        (
            12,
            "delete_learning_path",
            "Delete Learning Path",
            "Delete learning paths",
            "learning_path",
            "delete",
        ),
        (
            13,
            "publish_learning_path",
            "Publish Learning Path",
            "Publish learning paths",
            "learning_path",
            "publish",
        ),
        # Certificate permissions
        (
            14,
            "create_certificate_template",
            "Create Certificate Template",
            "Create certificate templates",
            "certificate",
            "create",
        ),
        (
            15,
            "edit_certificate_template",
            "Edit Certificate Template",
            "Edit certificate templates",
            "certificate",
            "update",
        ),
        (
            16,
            "delete_certificate_template",
            "Delete Certificate Template",
            "Delete certificate templates",
            "certificate",
            "delete",
        ),
        (
            17,
            "issue_certificate",
            "Issue Certificate",
            "Issue certificates to students",
            "certificate",
            "issue",
        ),
        # Live Class permissions
        (
            18,
            "create_live_class",
            "Create Live Class",
            "Schedule live classes",
            "live_class",
            "create",
        ),
        (
            19,
            "start_live_class",
            "Start Live Class",
            "Start live class sessions",
            "live_class",
            "start",
        ),
        (
            20,
            "end_live_class",
            "End Live Class",
            "End live class sessions",
            "live_class",
            "end",
        ),
        (
            21,
            "join_live_class",
            "Join Live Class",
            "Join live class as participant",
            "live_class",
            "join",
        ),
        # Discussion permissions
        (
            22,
            "moderate_discussion",
            "Moderate Discussion",
            "Moderate forum discussions",
            "discussion",
            "moderate",
        ),
        (
            23,
            "delete_post",
            "Delete Post",
            "Delete discussion posts",
            "discussion",
            "delete",
        ),
        (24, "pin_thread", "Pin Thread", "Pin discussion threads", "discussion", "pin"),
        # User management permissions
        (
            25,
            "manage_users",
            "Manage Users",
            "Create, edit, delete users",
            "user",
            "manage",
        ),
        (26, "ban_user", "Ban User", "Ban users from platform", "user", "ban"),
        (
            27,
            "assign_roles",
            "Assign Roles",
            "Assign roles to users",
            "user",
            "assign_role",
        ),
        # Question Bank permissions
        (
            28,
            "create_question_bank",
            "Create Question Bank",
            "Create question banks",
            "question_bank",
            "create",
        ),
        (
            29,
            "edit_question_bank",
            "Edit Question Bank",
            "Edit question banks",
            "question_bank",
            "update",
        ),
        (
            30,
            "delete_question_bank",
            "Delete Question Bank",
            "Delete question banks",
            "question_bank",
            "delete",
        ),
        # Peer Review permissions
        (
            31,
            "create_peer_review",
            "Create Peer Review",
            "Create peer review assignments",
            "peer_review",
            "create",
        ),
        (
            32,
            "submit_peer_review",
            "Submit Peer Review",
            "Submit peer reviews",
            "peer_review",
            "submit",
        ),
        # Announcement permissions
        (
            33,
            "create_announcement",
            "Create Announcement",
            "Create course announcements",
            "announcement",
            "create",
        ),
        (
            34,
            "delete_announcement",
            "Delete Announcement",
            "Delete announcements",
            "announcement",
            "delete",
        ),
    ]

    op.bulk_insert(
        permissions_table,
        [
            {
                "id": p[0],
                "name": p[1],
                "display_name": p[2],
                "description": p[3],
                "resource": p[4],
                "action": p[5],
            }
            for p in permissions_data
        ],
    )

    # Assign permissions to roles
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )

    # Admin gets all permissions (IDs 1-34)
    admin_permissions = [{"role_id": 1, "permission_id": i} for i in range(1, 35)]

    # Instructor permissions
    instructor_permissions = [
        {"role_id": 2, "permission_id": i}
        for i in [
            1,
            2,
            4,  # create, edit, publish course
            6,
            7,
            8,  # create, grade, delete assignment
            10,
            11,
            13,  # create, edit, publish learning path
            14,
            15,
            17,  # create, edit, issue certificate
            18,
            19,
            20,  # create, start, end live class
            22,
            24,  # moderate discussion, pin thread
            28,
            29,  # create, edit question bank
            31,  # create peer review
            33,  # create announcement
        ]
    ]

    # Student permissions
    student_permissions = [
        {"role_id": 3, "permission_id": i}
        for i in [
            9,  # submit assignment
            21,  # join live class
            32,  # submit peer review
        ]
    ]

    # Moderator permissions
    moderator_permissions = [
        {"role_id": 4, "permission_id": i}
        for i in [
            22,
            23,
            24,  # moderate, delete post, pin thread
        ]
    ]

    op.bulk_insert(
        role_permissions_table,
        admin_permissions
        + instructor_permissions
        + student_permissions
        + moderator_permissions,
    )

    # Assign default student role to all existing users
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM users"))
    user_ids = [row[0] for row in result.fetchall()]

    if user_ids:
        user_roles_table = sa.table(
            "user_roles",
            sa.column("user_id", sa.Integer),
            sa.column("role_id", sa.Integer),
        )
        op.bulk_insert(
            user_roles_table,
            [
                {"user_id": user_id, "role_id": 3}  # Assign student role (ID 3)
                for user_id in user_ids
            ],
        )


def downgrade() -> None:
    """Downgrade schema: Drop permissions system tables."""
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_permissions_action"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_resource"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_name"), table_name="permissions")
    op.drop_table("permissions")
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")
