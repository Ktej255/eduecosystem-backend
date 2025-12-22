"""Merge migration heads

Revision ID: b87d1b89cae2
Revises: 4bdd45ce4501, add_marketplace_models
Create Date: 2025-11-26 10:17:46.534212

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "b87d1b89cae2"
down_revision: Union[str, Sequence[str], None] = (
    "72a707a51302"  # Social learning (already applied branch point)
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
