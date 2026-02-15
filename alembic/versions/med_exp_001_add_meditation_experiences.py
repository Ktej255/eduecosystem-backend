"""Add meditation experiences table for AI progress tracking

Revision ID: med_exp_001
Revises: f7f44d322167
Create Date: 2026-02-02 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'med_exp_001'
down_revision: Union[str, Sequence[str], None] = '575d9bd6123e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Meditation Experiences
    if 'meditation_experiences' not in tables:
        op.create_table('meditation_experiences',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('day_completion_id', sa.Integer(), nullable=False),
            
            # Pre-session mental state
            sa.Column('pre_stress_level', sa.Integer(), nullable=False),
            sa.Column('pre_anxiety_level', sa.Integer(), nullable=False),
            sa.Column('pre_focus_level', sa.Integer(), nullable=False),
            sa.Column('pre_emotional_state', sa.String(length=50), nullable=False),
            sa.Column('pre_concerns', sa.Text(), nullable=True),
            sa.Column('pre_recorded_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            
            # Post-session mental state
            sa.Column('post_stress_level', sa.Integer(), nullable=True),
            sa.Column('post_anxiety_level', sa.Integer(), nullable=True),
            sa.Column('post_focus_level', sa.Integer(), nullable=True),
            sa.Column('post_emotional_state', sa.String(length=50), nullable=True),
            sa.Column('post_insights', sa.Text(), nullable=True),
            sa.Column('post_effectiveness_rating', sa.Integer(), nullable=True),
            sa.Column('post_recorded_at', sa.DateTime(timezone=True), nullable=True),
            
            # Calculated improvement metrics
            sa.Column('stress_improvement', sa.Integer(), nullable=True),
            sa.Column('anxiety_improvement', sa.Integer(), nullable=True),
            sa.Column('focus_improvement', sa.Integer(), nullable=True),
            sa.Column('overall_improvement_score', sa.Float(), nullable=True),
            
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['day_completion_id'], ['meditation_day_completions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_meditation_experiences_id'), 'meditation_experiences', ['id'], unique=False)
        op.create_index(op.f('ix_meditation_experiences_user_id'), 'meditation_experiences', ['user_id'], unique=False)
        op.create_index(op.f('ix_meditation_experiences_day_completion_id'), 'meditation_experiences', ['day_completion_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_meditation_experiences_day_completion_id'), table_name='meditation_experiences')
    op.drop_index(op.f('ix_meditation_experiences_user_id'), table_name='meditation_experiences')
    op.drop_index(op.f('ix_meditation_experiences_id'), table_name='meditation_experiences')
    op.drop_table('meditation_experiences')
