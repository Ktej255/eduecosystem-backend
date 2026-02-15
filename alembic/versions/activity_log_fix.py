"""Add missing fields to activity_logs table

Revision ID: activity_log_fix
Revises: user_fields_fix
Create Date: 2026-02-03 23:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'activity_log_fix'
down_revision = 'user_fields_fix'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns for activity_logs table
    op.add_column('activity_logs', sa.Column('ip_address', sa.String(), nullable=True))
    op.add_column('activity_logs', sa.Column('user_agent', sa.String(), nullable=True))


def downgrade():
    op.drop_column('activity_logs', 'user_agent')
    op.drop_column('activity_logs', 'ip_address')
