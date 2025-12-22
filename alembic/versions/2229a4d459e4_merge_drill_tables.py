"""merge_drill_tables

Revision ID: 2229a4d459e4
Revises: 6800b49d35ba, create_drill_tables
Create Date: 2025-12-11 18:56:01.510409

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2229a4d459e4'
down_revision: Union[str, Sequence[str], None] = ('6800b49d35ba', 'create_drill_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
