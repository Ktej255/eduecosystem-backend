"""Add pdf_data to Batch1Segment

Revision ID: bf987f61468a
Revises: 6f505c9472b1
Create Date: 2026-01-03 17:54:29.753720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf987f61468a'
down_revision: Union[str, Sequence[str], None] = '6f505c9472b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists to avoid errors (sqlite specific safety, valid for postgres too)
    op.add_column('batch1_segments', sa.Column('pdf_data', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('batch1_segments', 'pdf_data')
