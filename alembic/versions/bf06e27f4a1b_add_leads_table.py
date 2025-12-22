"""Add leads table

Revision ID: bf06e27f4a1b
Revises: 2229a4d459e4
Create Date: 2025-12-17 08:29:04.441575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf06e27f4a1b'
down_revision: Union[str, Sequence[str], None] = '2229a4d459e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create leads table."""
    op.create_table('leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('source_primary', sa.String(), nullable=True),
        sa.Column('source_secondary', sa.String(), nullable=True),
        sa.Column('source_tertiary', sa.String(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_method', sa.String(), nullable=True),
        sa.Column('intent_score', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_name'), 'leads', ['name'], unique=False)
    op.create_index(op.f('ix_leads_source_primary'), 'leads', ['source_primary'], unique=False)


def downgrade() -> None:
    """Drop leads table."""
    op.drop_index(op.f('ix_leads_source_primary'), table_name='leads')
    op.drop_index(op.f('ix_leads_name'), table_name='leads')
    op.drop_index(op.f('ix_leads_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_email'), table_name='leads')
    op.drop_table('leads')
