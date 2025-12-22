"""Merge marketing automation and mobile CRM heads

Revision ID: 2f618313c857
Revises: d2345678901b, mobile_crm_001
Create Date: 2025-12-17 08:55:25.408039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f618313c857'
down_revision: Union[str, Sequence[str], None] = ('d2345678901b', 'mobile_crm_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
