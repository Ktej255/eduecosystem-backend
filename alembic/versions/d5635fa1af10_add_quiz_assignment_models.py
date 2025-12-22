"""add_quiz_assignment_models

Revision ID: d5635fa1af10
Revises: cda7dfdd71b9
Create Date: 2025-11-22 10:39:55.197507

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5635fa1af10"
down_revision: Union[str, Sequence[str], None] = "cda7dfdd71b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to quizzes table
    op.add_column(
        "quizzes", sa.Column("time_limit_minutes", sa.Integer(), nullable=True)
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "passing_score_percentage", sa.Integer(), server_default="70", nullable=True
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column("allow_retakes", sa.Boolean(), server_default="true", nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "shuffle_questions", sa.Boolean(), server_default="true", nullable=True
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "show_correct_answers", sa.Boolean(), server_default="true", nullable=True
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
    )

    # Create quiz_attempts table
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("score_percentage", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("answers", sa.JSON(), server_default="{}", nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quiz_attempts_quiz_id"), "quiz_attempts", ["quiz_id"], unique=False
    )
    op.create_index(
        op.f("ix_quiz_attempts_user_id"), "quiz_attempts", ["user_id"], unique=False
    )

    # Create assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("max_score", sa.Integer(), server_default="100", nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column(
            "allow_late_submission", sa.Boolean(), server_default="true", nullable=True
        ),
        sa.Column("submission_type", sa.String(), server_default="file", nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assignments_lesson_id"), "assignments", ["lesson_id"], unique=False
    )

    # Create assignment_submissions table
    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("submission_text", sa.Text(), nullable=True),
        sa.Column("submission_url", sa.String(), nullable=True),
        sa.Column("attachment_url", sa.String(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("graded_at", sa.DateTime(), nullable=True),
        sa.Column("graded_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="submitted", nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["graded_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assignment_submissions_assignment_id"),
        "assignment_submissions",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assignment_submissions_user_id"),
        "assignment_submissions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.drop_index(
        op.f("ix_assignment_submissions_user_id"), table_name="assignment_submissions"
    )
    op.drop_index(
        op.f("ix_assignment_submissions_assignment_id"),
        table_name="assignment_submissions",
    )
    op.drop_table("assignment_submissions")

    op.drop_index(op.f("ix_assignments_lesson_id"), table_name="assignments")
    op.drop_table("assignments")

    op.drop_index(op.f("ix_quiz_attempts_user_id"), table_name="quiz_attempts")
    op.drop_index(op.f("ix_quiz_attempts_quiz_id"), table_name="quiz_attempts")
    op.drop_table("quiz_attempts")

    # Drop columns from quizzes table
    op.drop_column("quizzes", "updated_at")
    op.drop_column("quizzes", "created_at")
    op.drop_column("quizzes", "show_correct_answers")
    op.drop_column("quizzes", "shuffle_questions")
    op.drop_column("quizzes", "max_attempts")
    op.drop_column("quizzes", "allow_retakes")
    op.drop_column("quizzes", "passing_score_percentage")
    op.drop_column("quizzes", "time_limit_minutes")
