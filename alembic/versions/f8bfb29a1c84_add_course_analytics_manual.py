"""add_course_analytics_manual

Revision ID: f8bfb29a1c84
Revises: add_lms_models
Create Date: 2025-11-22 10:00:34.248617

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8bfb29a1c84"
down_revision: Union[str, Sequence[str], None] = "add_lms_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "course_analytics",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("total_enrollments", sa.Integer(), nullable=True),
        sa.Column("enrollments_this_month", sa.Integer(), nullable=True),
        sa.Column("total_revenue", sa.Float(), nullable=True),
        sa.Column("revenue_this_month", sa.Float(), nullable=True),
        sa.Column("avg_completion_rate", sa.Float(), nullable=True),
        sa.Column("avg_time_spent_minutes", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
        ),
        sa.PrimaryKeyConstraint("course_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("course_analytics")
