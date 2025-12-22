"""merge migration heads

Revision ID: 0d0a0825c46c
Revises: 40b1d24c652d, add_enterprise_sso
Create Date: 2025-11-26 11:54:50.120611

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "0d0a0825c46c"
down_revision: Union[str, Sequence[str], None] = ("40b1d24c652d", "add_enterprise_sso")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
