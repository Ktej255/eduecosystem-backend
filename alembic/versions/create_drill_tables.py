"""
Database migration for Drill System
Creates tables for questions, content, sessions, and analytics

Revision ID: create_drill_tables
Revises: 
Create Date: 2025-12-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = 'create_drill_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # DrillQuestion table
    op.create_table(
        'drill_questions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('gs_paper', sa.String(10), nullable=False, index=True),
        sa.Column('topic', sa.String(255), nullable=False, index=True),
        sa.Column('sub_topic', sa.String(255)),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('key_points', JSONB),
        sa.Column('difficulty', sa.String(20), default='medium'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # DrillContent table
    op.create_table(
        'drill_content',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('sections', JSONB, nullable=False),
        sa.Column('estimated_reading_time', sa.Integer, default=60),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['question_id'], ['drill_questions.id'], ondelete='CASCADE')
    )

    # DrillModelAnswer table
    op.create_table(
        'drill_model_answers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('question_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('answer_text', sa.Text, nullable=False),
        sa.Column('key_points', JSONB),
        sa.Column('word_count', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['question_id'], ['drill_questions.id'], ondelete='CASCADE')
    )

    # DrillSession table
    op.create_table(
        'drill_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('date', sa.Date, nullable=False, index=True),
        sa.Column('question_id', UUID(as_uuid=True), nullable=False),
        sa.Column('question_number', sa.Integer, nullable=False),
        sa.Column('before_answer_text', sa.Text),
        sa.Column('before_answer_image_url', sa.String(500)),
        sa.Column('after_answer_text', sa.Text),
        sa.Column('after_answer_image_url', sa.String(500)),
        sa.Column('question_read_time', sa.Integer),
        sa.Column('before_writing_time', sa.Integer),
        sa.Column('content_reading_time', sa.Integer),
        sa.Column('after_writing_time', sa.Integer),
        sa.Column('model_answer_time', sa.Integer),
        sa.Column('before_score', sa.Integer),
        sa.Column('after_score', sa.Integer),
        sa.Column('improvement', sa.Integer),
        sa.Column('overall_score', sa.Integer),
        sa.Column('report_data', JSONB),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['drill_questions.id'], ondelete='CASCADE')
    )

    # DrillDailySummary table
    op.create_table(
        'drill_daily_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('date', sa.Date, nullable=False, index=True),
        sa.Column('overall_score', sa.Integer),
        sa.Column('average_improvement', sa.Integer),
        sa.Column('total_time_spent', sa.Integer),
        sa.Column('question_scores', JSONB),
        sa.Column('comparison_data', JSONB),
        sa.Column('strengths', ARRAY(sa.Text)),
        sa.Column('challenges', ARRAY(sa.Text)),
        sa.Column('recommendations', ARRAY(sa.Text)),
        sa.Column('insights', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE')
    )

    # StudentActivity table
    op.create_table(
        'student_activities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), index=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('activity_data', JSONB),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), index=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['drill_sessions.id'], ondelete='CASCADE')
    )

    # CurriculumInsight table
    op.create_table(
        'curriculum_insights',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date, nullable=False, index=True),
        sa.Column('gs_paper', sa.String(10), index=True),
        sa.Column('total_students', sa.Integer),
        sa.Column('average_score', sa.Float),
        sa.Column('common_challenges', ARRAY(sa.Text)),
        sa.Column('high_performing_topics', ARRAY(sa.Text)),
        sa.Column('low_performing_topics', ARRAY(sa.Text)),
        sa.Column('ai_recommendations', JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('curriculum_insights')
    op.drop_table('student_activities')
    op.drop_table('drill_daily_summaries')
    op.drop_table('drill_sessions')
    op.drop_table('drill_model_answers')
    op.drop_table('drill_content')
    op.drop_table('drill_questions')
