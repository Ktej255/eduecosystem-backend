"""add_missing_user_fields_final

Revision ID: 123ba63c2f71
Revises: activity_log_fix
Create Date: 2026-02-27 21:05:56.599610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '123ba63c2f71'
down_revision: Union[str, Sequence[str], None] = 'activity_log_fix'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - safely add missing columns if they don't exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    # Subscription & Payments
    if "is_premium" not in columns:
        op.add_column("users", sa.Column("is_premium", sa.Boolean(), server_default='false'))
    if "cashfree_customer_id" not in columns:
        op.add_column("users", sa.Column("cashfree_customer_id", sa.String(), nullable=True))
    if "subscription_status" not in columns:
        op.add_column("users", sa.Column("subscription_status", sa.String(), server_default="'free'"))
    
    # Graphotherapy
    if "graphotherapy_enrollment_date" not in columns:
        op.add_column("users", sa.Column("graphotherapy_enrollment_date", sa.DateTime(timezone=True), nullable=True))
    if "is_graphotherapy_exclusive" not in columns:
        op.add_column("users", sa.Column("is_graphotherapy_exclusive", sa.Boolean(), server_default='false'))
    
    # Organization / SSO
    if "organization_id" not in columns:
        op.add_column("users", sa.Column("organization_id", sa.Integer(), nullable=True))
        # Note: If organizations table is missing, the FK might crash, but let's assume it exists or use raw SQL to skip it if unstable.
    if "is_sso_user" not in columns:
        op.add_column("users", sa.Column("is_sso_user", sa.Boolean(), server_default='false'))
    if "sso_external_id" not in columns:
        op.add_column("users", sa.Column("sso_external_id", sa.String(), nullable=True))
    
    # Authorizations & Flags
    if "is_verified" not in columns:
        op.add_column("users", sa.Column("is_verified", sa.Boolean(), server_default='false'))
    if "is_ras_authorized" not in columns:
        op.add_column("users", sa.Column("is_ras_authorized", sa.Boolean(), server_default='false'))
    if "is_batch1_authorized" not in columns:
        op.add_column("users", sa.Column("is_batch1_authorized", sa.Boolean(), server_default='false'))
    if "is_batch2_authorized" not in columns:
        op.add_column("users", sa.Column("is_batch2_authorized", sa.Boolean(), server_default='false'))
    
    # Security
    if "totp_secret" not in columns:
        op.add_column("users", sa.Column("totp_secret", sa.String(), nullable=True))
        
    # Revision Portal & Settings
    if "revision_level" not in columns:
        op.add_column("users", sa.Column("revision_level", sa.String(), nullable=True))
    if "revision_exam_id" not in columns:
        op.add_column("users", sa.Column("revision_exam_id", sa.String(), nullable=True))
    if "push_subscription" not in columns:
        op.add_column("users", sa.Column("push_subscription", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
