"""force ras

Revision ID: 9c9157d5ac63
Revises: 9eed3ff38601
Create Date: 2026-01-02 23:22:37.206885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c9157d5ac63'
down_revision: Union[str, Sequence[str], None] = '9eed3ff38601'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_ras_authorized to users table
    # Using batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_ras_authorized', sa.Boolean(), nullable=True, server_default='0'))
    
    # Create ras_topic_progress table
    op.create_table('ras_topic_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.String(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('hours_spent', sa.Float(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('summary_text', sa.String(), nullable=True),
        sa.Column('mastery_level', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ras_topic_progress_id'), 'ras_topic_progress', ['id'], unique=False)
    op.create_index(op.f('ix_ras_topic_progress_topic_id'), 'ras_topic_progress', ['topic_id'], unique=False)
    op.create_index(op.f('ix_ras_topic_progress_user_id'), 'ras_topic_progress', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ras_topic_progress_user_id'), table_name='ras_topic_progress')
    op.drop_index(op.f('ix_ras_topic_progress_topic_id'), table_name='ras_topic_progress')
    op.drop_index(op.f('ix_ras_topic_progress_id'), table_name='ras_topic_progress')
    # op.drop_table('ras_topic_progress')
    # Use batch for users drop column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_ras_authorized')
    op.drop_table('ras_topic_progress')
