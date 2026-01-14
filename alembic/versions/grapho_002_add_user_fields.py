"""add_graphotherapy_user_fields

Revision ID: grapho_002
Revises: 0d0a0825c46c
Create Date: 2026-01-14 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'grapho_002'
down_revision = '0d0a0825c46c'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to 'users' table
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('graphotherapy_enrollment_date', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_graphotherapy_exclusive', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    
    # Optional: Fill created_at for existing users with now
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL")


def downgrade():
    op.drop_column('users', 'is_graphotherapy_exclusive')
    op.drop_column('users', 'graphotherapy_enrollment_date')
    op.drop_column('users', 'created_at')
