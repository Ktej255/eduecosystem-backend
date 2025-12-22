"""Add user management tables

Revision ID: c1234567890a
Revises: bf06e27f4a1b
Create Date: 2025-12-17 08:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1234567890a'
down_revision: Union[str, Sequence[str], None] = 'bf06e27f4a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user management tables."""
    # Data Masking Config Table
    op.create_table('data_masking_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('mask_email', sa.Boolean(), nullable=True),
        sa.Column('mask_phone', sa.Boolean(), nullable=True),
        sa.Column('mask_address', sa.Boolean(), nullable=True),
        sa.Column('mask_financial', sa.Boolean(), nullable=True),
        sa.Column('custom_masked_fields', sa.JSON(), nullable=True),
        sa.Column('masking_pattern', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_masking_configs_id'), 'data_masking_configs', ['id'], unique=False)
    op.create_index(op.f('ix_data_masking_configs_role'), 'data_masking_configs', ['role'], unique=False)
    op.create_index(op.f('ix_data_masking_configs_user_id'), 'data_masking_configs', ['user_id'], unique=False)

    # User Permissions Table
    op.create_table('user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('can_view_leads', sa.Boolean(), nullable=True),
        sa.Column('can_edit_leads', sa.Boolean(), nullable=True),
        sa.Column('can_delete_leads', sa.Boolean(), nullable=True),
        sa.Column('can_reassign_leads', sa.Boolean(), nullable=True),
        sa.Column('can_export_leads', sa.Boolean(), nullable=True),
        sa.Column('can_manage_users', sa.Boolean(), nullable=True),
        sa.Column('can_view_activity_logs', sa.Boolean(), nullable=True),
        sa.Column('can_manage_permissions', sa.Boolean(), nullable=True),
        sa.Column('can_send_emails', sa.Boolean(), nullable=True),
        sa.Column('can_send_sms', sa.Boolean(), nullable=True),
        sa.Column('can_make_calls', sa.Boolean(), nullable=True),
        sa.Column('can_view_reports', sa.Boolean(), nullable=True),
        sa.Column('can_export_reports', sa.Boolean(), nullable=True),
        sa.Column('can_view_analytics', sa.Boolean(), nullable=True),
        sa.Column('can_view_payments', sa.Boolean(), nullable=True),
        sa.Column('can_process_refunds', sa.Boolean(), nullable=True),
        sa.Column('custom_permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_permissions_id'), 'user_permissions', ['id'], unique=False)
    op.create_index(op.f('ix_user_permissions_user_id'), 'user_permissions', ['user_id'], unique=False)

    # User Sessions Table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('device_info', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('login_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('logout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop user management tables."""
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_session_token'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.drop_table('user_sessions')
    
    op.drop_index(op.f('ix_user_permissions_user_id'), table_name='user_permissions')
    op.drop_index(op.f('ix_user_permissions_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    
    op.drop_index(op.f('ix_data_masking_configs_user_id'), table_name='data_masking_configs')
    op.drop_index(op.f('ix_data_masking_configs_role'), table_name='data_masking_configs')
    op.drop_index(op.f('ix_data_masking_configs_id'), table_name='data_masking_configs')
    op.drop_table('data_masking_configs')
