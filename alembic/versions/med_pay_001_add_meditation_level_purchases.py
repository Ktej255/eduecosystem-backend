"""Add meditation level purchases

Revision ID: med_pay_001
Revises: med_exp_001
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'med_pay_001'
down_revision = 'med_exp_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create meditation_level_purchases table
    op.create_table(
        'meditation_level_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='INR'),
        sa.Column('discount_applied', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('payment_gateway', sa.String(length=50), nullable=False),
        sa.Column('payment_id', sa.String(length=255), nullable=False),
        sa.Column('order_id', sa.String(length=255), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('purchased_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('razorpay_signature', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('payment_id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_meditation_level_purchases_id'), 'meditation_level_purchases', ['id'], unique=False)
    op.create_index(op.f('ix_meditation_level_purchases_user_id'), 'meditation_level_purchases', ['user_id'], unique=False)
    op.create_index(op.f('ix_meditation_level_purchases_level'), 'meditation_level_purchases', ['level'], unique=False)
    op.create_index(op.f('ix_meditation_level_purchases_payment_status'), 'meditation_level_purchases', ['payment_status'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_meditation_level_purchases_payment_status'), table_name='meditation_level_purchases')
    op.drop_index(op.f('ix_meditation_level_purchases_level'), table_name='meditation_level_purchases')
    op.drop_index(op.f('ix_meditation_level_purchases_user_id'), table_name='meditation_level_purchases')
    op.drop_index(op.f('ix_meditation_level_purchases_id'), table_name='meditation_level_purchases')
    
    # Drop table
    op.drop_table('meditation_level_purchases')
