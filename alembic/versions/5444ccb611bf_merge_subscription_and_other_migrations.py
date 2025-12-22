"""merge subscription and other migrations

Revision ID: 5444ccb611bf
Revises: 0d0a0825c46c, sub_001
Create Date: 2025-11-26 12:00:44.615542

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "5444ccb611bf"
down_revision: Union[str, Sequence[str], None] = ("0d0a0825c46c", "sub_001")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
