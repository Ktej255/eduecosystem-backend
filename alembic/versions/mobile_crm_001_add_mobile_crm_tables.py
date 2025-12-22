"""Add mobile CRM tables (field_activities, call_logs, voice_notes)

Revision ID: mobile_crm_001
Revises: 
Create Date: 2025-12-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'mobile_crm_001'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add location fields to leads table
    op.add_column('leads', sa.Column('location_latitude', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('location_longitude', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('location_address', sa.String(), nullable=True))

    # Create field_activities table
    op.create_table(
        'field_activities',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('activity_type', sa.String(50), nullable=False, index=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=True, index=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('route_distance_km', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create call_logs table
    op.create_table(
        'call_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False, index=True),
        sa.Column('call_type', sa.String(20), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), default=0),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('call_started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('call_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create voice_notes table
    op.create_table(
        'voice_notes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=True, index=True),
        sa.Column('field_activity_id', sa.Integer(), sa.ForeignKey('field_activities.id'), nullable=True, index=True),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('voice_notes')
    op.drop_table('call_logs')
    op.drop_table('field_activities')
    op.drop_column('leads', 'location_address')
    op.drop_column('leads', 'location_longitude')
    op.drop_column('leads', 'location_latitude')
