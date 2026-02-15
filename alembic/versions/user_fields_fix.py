"""Add missing fields to users table

Revision ID: user_fields_fix
Revises: med_pay_001
Create Date: 2026-02-03 23:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'user_fields_fix'
down_revision = 'med_pay_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to 'users' table
    # Check if column exists before adding to prevent errors if partial migration happened
    
    # TOTP Secret for 2FA
    op.add_column('users', sa.Column('totp_secret', sa.String(), nullable=True))
    
    # Revision Portal Preferences
    op.add_column('users', sa.Column('revision_level', sa.String(), nullable=True))
    op.add_column('users', sa.Column('revision_exam_id', sa.String(), nullable=True))
    
    # Push Notifications (JSON for VAPID/Subscription data)
    op.add_column('users', sa.Column('push_subscription', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('users', 'push_subscription')
    op.drop_column('users', 'revision_exam_id')
    op.drop_column('users', 'revision_level')
    op.drop_column('users', 'totp_secret')
