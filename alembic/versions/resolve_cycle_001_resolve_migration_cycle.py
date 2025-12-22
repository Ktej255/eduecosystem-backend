"""resolve_migration_cycle

Revision ID: resolve_cycle_001
Revises: 0d0a0825c46c, 25a62f76c84f
Create Date: 2025-11-28 09:00:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "resolve_cycle_001"
down_revision: Union[str, Sequence[str], None] = ("0d0a0825c46c", "25a62f76c84f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
