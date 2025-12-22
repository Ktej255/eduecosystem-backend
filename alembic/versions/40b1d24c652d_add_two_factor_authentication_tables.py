"""Add two-factor authentication tables

Revision ID: 40b1d24c652d
Revises: b87d1b89cae2
Create Date: 2025-11-26 10:29:14.060801

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "40b1d24c652d"
down_revision: Union[str, Sequence[str], None] = "b87d1b89cae2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add 2FA tables only."""
    # Create two_factor_auth table
    op.create_table(
        "two_factor_auth",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("two_factor_auth", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_two_factor_auth_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_two_factor_auth_user_id"), ["user_id"], unique=True
        )

    # Create two_factor_backup_codes table
    op.create_table(
        "two_factor_backup_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("two_factor_auth_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["two_factor_auth_id"],
            ["two_factor_auth.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("two_factor_backup_codes", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_two_factor_backup_codes_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_two_factor_backup_codes_user_id"), ["user_id"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema - Remove 2FA tables."""
    with op.batch_alter_table("two_factor_backup_codes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_two_factor_backup_codes_user_id"))
        batch_op.drop_index(batch_op.f("ix_two_factor_backup_codes_id"))

    op.drop_table("two_factor_backup_codes")

    with op.batch_alter_table("two_factor_auth", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_two_factor_auth_user_id"))
        batch_op.drop_index(batch_op.f("ix_two_factor_auth_id"))

    op.drop_table("two_factor_auth")
