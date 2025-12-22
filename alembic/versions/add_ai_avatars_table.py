"""
Create AI Avatars Table Migration

Revision ID: add_ai_avatars_table
Revises: 
Create Date: 2024-11-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_ai_avatars_table'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_avatars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purpose', sa.String(length=50), nullable=False),
        sa.Column('personality', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(length=50), nullable=True),
        sa.Column('response_style', sa.String(length=50), nullable=True),
        sa.Column('knowledge_base', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_avatars_id'), 'ai_avatars', ['id'], unique=False)
    op.create_index(op.f('ix_ai_avatars_user_id'), 'ai_avatars', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ai_avatars_user_id'), table_name='ai_avatars')
    op.drop_index(op.f('ix_ai_avatars_id'), table_name='ai_avatars')
    op.drop_table('ai_avatars')
