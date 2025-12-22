"""add subscription tables

Revision ID: sub_001
Revises: 0d0a0825c46c
Create Date: 2025-11-26 11:53:00

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "sub_001"
down_revision: Union[str, Sequence[str], None] = "b87d1b89cae2"  # Current head
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add subscription tables."""

    # Create subscription_plans table
    # op.create_table('subscription_plans',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('name', sa.String(length=100), nullable=False),
    #     sa.Column('slug', sa.String(length=100), nullable=False),
    #     sa.Column('description', sa.Text(), nullable=True),
    #     sa.Column('short_description', sa.String(length=500), nullable=True),
    #     sa.Column('monthly_price', sa.Numeric(precision=10, scale=2), nullable=False),
    #     sa.Column('yearly_price', sa.Numeric(precision=10, scale=2), nullable=True),
    #     sa.Column('currency', sa.String(length=3), nullable=True),
    #     sa.Column('trial_days', sa.Integer(), nullable=True),
    #     sa.Column('access_level', sa.String(length=20), nullable=True),
    #     sa.Column('max_courses', sa.Integer(), nullable=True),
    #     sa.Column('max_live_classes', sa.Integer(), nullable=True),
    #     sa.Column('features', sa.Text(), nullable=True),
    #     sa.Column('included_features', sa.Text(), nullable=True),
    #     sa.Column('is_active', sa.Boolean(), nullable=True),
    #     sa.Column('is_featured', sa.Boolean(), nullable=True),
    #     sa.Column('is_popular', sa.Boolean(), nullable=True),
    #     sa.Column('display_order', sa.Integer(), nullable=True),
    #     sa.Column('stripe_price_id_monthly', sa.String(length=100), nullable=True),
    #     sa.Column('stripe_price_id_yearly', sa.String(length=100), nullable=True),
    #     sa.Column('stripe_product_id', sa.String(length=100), nullable=True),
    #     sa.Column('total_subscriptions', sa.Integer(), nullable=True),
    #     sa.Column('active_subscriptions', sa.Integer(), nullable=True),
    #     sa.Column('total_revenue', sa.Numeric(precision=10, scale=2), nullable=True),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # with op.batch_alter_table('subscription_plans', schema=None) as batch_op:
    #     batch_op.create_index(batch_op.f('ix_subscription_plans_id'), ['id'], unique=False)
    #     batch_op.create_index(batch_op.f('ix_subscription_plans_slug'), ['slug'], unique=True)
    #     batch_op.create_index('ix_subscription_plans_name', ['name'], unique=True)

    # # Create user_subscriptions table
    # op.create_table('user_subscriptions',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('user_id', sa.Integer(), nullable=False),
    #     sa.Column('plan_id', sa.Integer(), nullable=False),
    #     sa.Column('billing_cycle', sa.String(length=20), nullable=False),
    #     sa.Column('status', sa.String(length=20), nullable=False),
    #     sa.Column('started_at', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
    #     sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
    #     sa.Column('stripe_latest_invoice', sa.String(length=100), nullable=True),
    #     sa.Column('price_paid', sa.Numeric(precision=10, scale=2), nullable=False),
    #     sa.Column('currency', sa.String(length=3), nullable=True),
    #     sa.Column('auto_renew', sa.Boolean(), nullable=True),
    #     sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True),
    #     sa.Column('last_payment_date', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('next_payment_date', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('payment_failed_count', sa.Integer(), nullable=True),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
    #     sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    #     sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # with op.batch_alter_table('user_subscriptions', schema=None) as batch_op:
    #     batch_op.create_index(batch_op.f('ix_user_subscriptions_id'), ['id'], unique=False)
    #     batch_op.create_index(batch_op.f('ix_user_subscriptions_user_id'), ['user_id'], unique=False)
    #     batch_op.create_index(batch_op.f('ix_user_subscriptions_plan_id'), ['plan_id'], unique=False)
    #     batch_op.create_index('ix_user_subscriptions_stripe_subscription_id', ['stripe_subscription_id'], unique=True)

    # # Create subscription_invoices table
    # op.create_table('subscription_invoices',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('subscription_id', sa.Integer(), nullable=False),
    #     sa.Column('invoice_number', sa.String(length=50), nullable=True),
    #     sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    #     sa.Column('currency', sa.String(length=3), nullable=True),
    #     sa.Column('status', sa.String(length=20), nullable=False),
    #     sa.Column('stripe_invoice_id', sa.String(length=100), nullable=True),
    #     sa.Column('stripe_payment_intent', sa.String(length=100), nullable=True),
    #     sa.Column('invoice_date', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('invoice_pdf_url', sa.String(length=500), nullable=True),
    #     sa.Column('description', sa.Text(), nullable=True),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
    #     sa.ForeignKeyConstraint(['subscription_id'], ['user_subscriptions.id'], ),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # with op.batch_alter_table('subscription_invoices', schema=None) as batch_op:
    #     batch_op.create_index(batch_op.f('ix_subscription_invoices_id'), ['id'], unique=False)
    #     batch_op.create_index(batch_op.f('ix_subscription_invoices_subscription_id'), ['subscription_id'], unique=False)
    #     batch_op.create_index('ix_subscription_invoices_invoice_number', ['invoice_number'], unique=True)
    #     batch_op.create_index('ix_subscription_invoices_stripe_invoice_id', ['stripe_invoice_id'], unique=True)

    # # Create subscription_coupons table
    # op.create_table('subscription_coupons',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('code', sa.String(length=50), nullable=False),
    #     sa.Column('name', sa.String(length=100), nullable=False),
    #     sa.Column('description', sa.Text(), nullable=True),
    #     sa.Column('discount_type', sa.String(length=20), nullable=False),
    #     sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=False),
    #     sa.Column('currency', sa.String(length=3), nullable=True),
    #     sa.Column('applies_to_plans', sa.Text(), nullable=True),
    #     sa.Column('duration', sa.String(length=20), nullable=False),
    #     sa.Column('duration_months', sa.Integer(), nullable=True),
    #     sa.Column('is_active', sa.Boolean(), nullable=True),
    #     sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
    #     sa.Column('max_redemptions', sa.Integer(), nullable=True),
    #     sa.Column('max_redemptions_per_user', sa.Integer(), nullable=True),
    #     sa.Column('times_redeemed', sa.Integer(), nullable=True),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    #     sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # with op.batch_alter_table('subscription_coupons', schema=None) as batch_op:
    #     batch_op.create_index(batch_op.f('ix_subscription_coupons_id'), ['id'], unique=False)
    #     batch_op.create_index(batch_op.f('ix_subscription_coupons_code'), ['code'], unique=True)
    pass


def downgrade() -> None:
    """Downgrade schema - Remove subscription tables."""
    op.drop_table("subscription_coupons")
    op.drop_table("subscription_invoices")
    op.drop_table("user_subscriptions")
    op.drop_table("subscription_plans")
