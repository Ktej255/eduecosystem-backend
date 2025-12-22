"""Add social learning and collaborative projects - manual

Revision ID: 72a707a51302
Revises: 9b0aabbee1b0
Create Date: 2025-11-25 23:03:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "72a707a51302"
down_revision: Union[str, Sequence[str], None] = "9b0aabbee1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add social learning tables only."""

    # Create LearningGroups table
    op.create_table(
        "learning_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "group_type",
            sa.Enum("STUDY", "PROJECT", "DISCUSSION", "PEER_SUPPORT", name="grouptype"),
            nullable=True,
        ),
        sa.Column(
            "privacy",
            sa.Enum("PUBLIC", "PRIVATE", "INVITE_ONLY", name="groupprivacy"),
            nullable=True,
        ),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("max_members", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_groups_id"), "learning_groups", ["id"], unique=False
    )

    # Create GroupMemberships table
    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "MODERATOR", "MEMBER", name="memberrole"),
            nullable=True,
        ),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["learning_groups.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_group_memberships_id"), "group_memberships", ["id"], unique=False
    )

    # Create GroupPosts table
    op.create_table(
        "group_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["learning_groups.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_group_posts_id"), "group_posts", ["id"], unique=False)

    # Create GroupPostComments table
    op.create_table(
        "group_post_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["group_posts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_group_post_comments_id"), "group_post_comments", ["id"], unique=False
    )

    # Create CollaborativeProjects table
    op.create_table(
        "collaborative_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PLANNING",
                "IN_PROGRESS",
                "SUBMITTED",
                "GRADED",
                "COMPLETED",
                name="projectstatus",
            ),
            nullable=False,
        ),
        sa.Column("max_team_size", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["group_id"], ["learning_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collaborative_projects_id"),
        "collaborative_projects",
        ["id"],
        unique=False,
    )

    # Create ProjectTeams table
    op.create_table(
        "project_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["collaborative_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_teams_id"), "project_teams", ["id"], unique=False)

    # Create ProjectMilestones table
    op.create_table(
        "project_milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["collaborative_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_milestones_id"), "project_milestones", ["id"], unique=False
    )

    # Create ProjectTeamMembers table
    op.create_table(
        "project_team_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role", sa.Enum("LEADER", "MEMBER", name="projectrole"), nullable=False
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["project_teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_team_members_id"), "project_team_members", ["id"], unique=False
    )

    # Create ProjectSubmissions table
    op.create_table(
        "project_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("grade", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("graded_by", sa.Integer(), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["graded_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["collaborative_projects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["project_teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_submissions_id"), "project_submissions", ["id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema - remove social learning tables."""
    op.drop_index(op.f("ix_project_submissions_id"), table_name="project_submissions")
    op.drop_table("project_submissions")
    op.drop_index(op.f("ix_project_team_members_id"), table_name="project_team_members")
    op.drop_table("project_team_members")
    op.drop_index(op.f("ix_project_milestones_id"), table_name="project_milestones")
    op.drop_table("project_milestones")
    op.drop_index(op.f("ix_project_teams_id"), table_name="project_teams")
    op.drop_table("project_teams")
    op.drop_index(
        op.f("ix_collaborative_projects_id"), table_name="collaborative_projects"
    )
    op.drop_table("collaborative_projects")
    op.drop_index(op.f("ix_group_post_comments_id"), table_name="group_post_comments")
    op.drop_table("group_post_comments")
    op.drop_index(op.f("ix_group_posts_id"), table_name="group_posts")
    op.drop_table("group_posts")
    op.drop_index(op.f("ix_group_memberships_id"), table_name="group_memberships")
    op.drop_table("group_memberships")
    op.drop_index(op.f("ix_learning_groups_id"), table_name="learning_groups")
    op.drop_table("learning_groups")
