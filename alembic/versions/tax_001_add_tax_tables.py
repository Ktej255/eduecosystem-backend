"""add tax tables

Revision ID: tax_001
Revises: sub_001
Create Date: 2025-11-26 12:04:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = "tax_001"
down_revision: Union[str, Sequence[str], None] = "sub_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add tax tables."""

    # Create tax_rates table
    op.create_table(
        "tax_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("state_code", sa.String(length=10), nullable=True),
        sa.Column("region_name", sa.String(length=100), nullable=False),
        sa.Column("tax_name", sa.String(length=50), nullable=False),
        sa.Column("tax_rate", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("tax_type", sa.String(length=20), nullable=False),
        sa.Column("applies_to_digital_goods", sa.Boolean(), nullable=True),
        sa.Column("applies_to_physical_goods", sa.Boolean(), nullable=True),
        sa.Column("applies_to_services", sa.Boolean(), nullable=True),
        sa.Column("applies_to_subscriptions", sa.Boolean(), nullable=True),
        sa.Column("is_compound", sa.Boolean(), nullable=True),
        sa.Column("compound_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tax_id_required", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tax_rates", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tax_rates_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_tax_rates_country_code"), ["country_code"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_tax_rates_state_code"), ["state_code"], unique=False
        )

    # Create tax_calculations table
    op.create_table(
        "tax_calculations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tax_rate_id", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("billing_country", sa.String(length=2), nullable=True),
        sa.Column("billing_state", sa.String(length=10), nullable=True),
        sa.Column("billing_zip", sa.String(length=20), nullable=True),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("tax_exempt", sa.Boolean(), nullable=True),
        sa.Column("tax_exempt_reason", sa.String(length=200), nullable=True),
        sa.Column("calculation_method", sa.String(length=50), nullable=True),
        sa.Column("is_inclusive", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tax_rate_id"],
            ["tax_rates.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tax_calculations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_tax_calculations_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_tax_calculations_user_id"), ["user_id"], unique=False
        )

    # Create tax_exemptions table
    op.create_table(
        "tax_exemptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("exemption_type", sa.String(length=50), nullable=False),
        sa.Column("exemption_certificate", sa.String(length=100), nullable=True),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("state_code", sa.String(length=10), nullable=True),
        sa.Column("applies_to_all", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certificate_url", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tax_exemptions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tax_exemptions_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_tax_exemptions_user_id"), ["user_id"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema - Remove tax tables."""
    op.drop_table("tax_exemptions")
    op.drop_table("tax_calculations")
    op.drop_table("tax_rates")
