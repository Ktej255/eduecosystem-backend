"""add_video_fields_manual

Revision ID: cda7dfdd71b9
Revises: f8bfb29a1c84
Create Date: 2025-11-22 10:22:22.135182

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cda7dfdd71b9"
down_revision: Union[str, Sequence[str], None] = "f8bfb29a1c84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "lessons",
        sa.Column("video_provider", sa.String(), server_default="local", nullable=True),
    )
    op.add_column("lessons", sa.Column("video_id", sa.String(), nullable=True))
    op.add_column(
        "lessons", sa.Column("video_thumbnail_url", sa.String(), nullable=True)
    )
    op.add_column(
        "lessons",
        sa.Column("video_status", sa.String(), server_default="ready", nullable=True),
    )
    op.add_column(
        "lessons", sa.Column("video_uploaded_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("lessons", "video_uploaded_at")
    op.drop_column("lessons", "video_status")
    op.drop_column("lessons", "video_thumbnail_url")
    op.drop_column("lessons", "video_id")
    op.drop_column("lessons", "video_provider")
