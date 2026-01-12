"""Add Graphotherapy and Meditation models

Revision ID: f7f44d322167
Revises: f73ef2a321c3
Create Date: 2026-01-11 11:45:59.445163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7f44d322167'
down_revision: Union[str, Sequence[str], None] = '9c9157d5ac63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Meditation Processes
    if 'meditation_processes' not in tables:
        op.create_table('meditation_processes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=True),
            sa.Column('video_url', sa.String(length=500), nullable=True),
            sa.Column('video_filename', sa.String(length=255), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('level', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('announcement_audio_url', sa.String(length=500), nullable=True),
            sa.Column('background_music_url', sa.String(length=500), nullable=True),
            sa.Column('bell_sound_url', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_meditation_processes_id'), 'meditation_processes', ['id'], unique=False)

    # Meditation Progress
    if 'meditation_progress' not in tables:
        op.create_table('meditation_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('current_level', sa.Integer(), nullable=True),
            sa.Column('current_day', sa.Integer(), nullable=True),
            sa.Column('total_streak', sa.Integer(), nullable=True),
            sa.Column('preferred_session', sa.String(length=20), nullable=True),
            sa.Column('last_practice_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_meditation_progress_id'), 'meditation_progress', ['id'], unique=False)

    # Meditation Day Completions
    if 'meditation_day_completions' not in tables:
        op.create_table('meditation_day_completions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('progress_id', sa.Integer(), nullable=False),
            sa.Column('level', sa.Integer(), nullable=False),
            sa.Column('day_number', sa.Integer(), nullable=False),
            sa.Column('session_type', sa.String(length=20), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('total_duration_minutes', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['progress_id'], ['meditation_progress.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_meditation_day_completions_id'), 'meditation_day_completions', ['id'], unique=False)

    # Meditation Process Completions
    if 'meditation_process_completions' not in tables:
        op.create_table('meditation_process_completions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('day_completion_id', sa.Integer(), nullable=False),
            sa.Column('process_id', sa.Integer(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('watched_video', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['day_completion_id'], ['meditation_day_completions.id'], ),
            sa.ForeignKeyConstraint(['process_id'], ['meditation_processes.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_meditation_process_completions_id'), 'meditation_process_completions', ['id'], unique=False)

    # Graphotherapy Progress
    if 'graphotherapy_progress' not in tables:
        op.create_table('graphotherapy_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('current_level', sa.Integer(), nullable=True),
            sa.Column('current_day', sa.Integer(), nullable=True),
            sa.Column('total_streak', sa.Integer(), nullable=True),
            sa.Column('last_practice_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_graphotherapy_progress_id'), 'graphotherapy_progress', ['id'], unique=False)

    # Graphotherapy Day Completions
    if 'graphotherapy_day_completions' not in tables:
        op.create_table('graphotherapy_day_completions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('progress_id', sa.Integer(), nullable=False),
            sa.Column('level', sa.Integer(), nullable=False),
            sa.Column('day_number', sa.Integer(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('upload_url', sa.String(length=500), nullable=True),
            sa.Column('upload_filename', sa.String(length=255), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['progress_id'], ['graphotherapy_progress.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_graphotherapy_day_completions_id'), 'graphotherapy_day_completions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_graphotherapy_day_completions_id'), table_name='graphotherapy_day_completions')
    op.drop_table('graphotherapy_day_completions')
    op.drop_index(op.f('ix_graphotherapy_progress_id'), table_name='graphotherapy_progress')
    op.drop_table('graphotherapy_progress')
    op.drop_index(op.f('ix_meditation_process_completions_id'), table_name='meditation_process_completions')
    op.drop_table('meditation_process_completions')
    op.drop_index(op.f('ix_meditation_day_completions_id'), table_name='meditation_day_completions')
    op.drop_table('meditation_day_completions')
    op.drop_index(op.f('ix_meditation_progress_id'), table_name='meditation_progress')
    op.drop_table('meditation_progress')
    op.drop_index(op.f('ix_meditation_processes_id'), table_name='meditation_processes')
    op.drop_table('meditation_processes')
