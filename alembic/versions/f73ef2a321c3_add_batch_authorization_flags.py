"""add_batch_authorization_flags

Revision ID: f73ef2a321c3
Revises: bf987f61468a
Create Date: 2026-01-03 18:31:29.562050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f73ef2a321c3'
down_revision: Union[str, Sequence[str], None] = 'bf987f61468a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_batch1_authorized', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('is_batch2_authorized', sa.Boolean(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_batch2_authorized')
        batch_op.drop_column('is_batch1_authorized')
