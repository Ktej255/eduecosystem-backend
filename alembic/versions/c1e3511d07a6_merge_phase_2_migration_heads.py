"""Merge Phase 2 migration heads

Revision ID: c1e3511d07a6
Revises: d5635fa1af10, performance_indexes
Create Date: 2025-11-23 23:45:22.727134

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c1e3511d07a6"
down_revision: Union[str, Sequence[str], None] = ("d5635fa1af10", "performance_indexes")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
