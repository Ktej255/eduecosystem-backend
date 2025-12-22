"""merge ai avatars and cycle resolution

Revision ID: bddea90f6eae
Revises: add_ai_avatars_table, resolve_cycle_001
Create Date: 2025-11-30 22:01:58.885342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bddea90f6eae'
down_revision: Union[str, Sequence[str], None] = ('add_ai_avatars_table', 'resolve_cycle_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
