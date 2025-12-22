"""merge_heads_for_cart

Revision ID: 25a62f76c84f
Revises: 5444ccb611bf, tax_001
Create Date: 2025-11-26 12:17:58.263017

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "25a62f76c84f"
down_revision: Union[str, Sequence[str], None] = ("5444ccb611bf", "tax_001")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
