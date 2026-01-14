"""merge_3_heads

Revision ID: 9b18277e8f32
Revises: f73ef2a321c3, f7f44d322167, grapho_002
Create Date: 2026-01-14 11:27:10.554357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b18277e8f32'
down_revision: Union[str, Sequence[str], None] = ('f73ef2a321c3', 'f7f44d322167', 'grapho_002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
