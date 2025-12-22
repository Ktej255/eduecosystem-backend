"""Add Enterprise SSO models

Revision ID: add_enterprise_sso
Revises:
Create Date: 2025-11-26

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_enterprise_sso"
down_revision = "4bdd45ce4501"  # Marketplace models
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("sso_enabled", sa.Boolean(), nullable=True, server_default="0"),
        sa.Column("sso_provider", sa.String(length=50), nullable=True),
        sa.Column("sso_enforced", sa.Boolean(), nullable=True, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_organizations_domain"), "organizations", ["domain"], unique=True
    )
    op.create_index(
        op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)

    # Create sso_configs table (using String instead of Enum for SQLite compatibility)
    op.create_table(
        "sso_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider_type", sa.String(length=20), nullable=False
        ),  # 'SAML', 'OIDC', 'OAUTH'
        sa.Column("provider_name", sa.String(length=100), nullable=True),
        # SAML fields
        sa.Column("entity_id", sa.String(length=500), nullable=True),
        sa.Column("idp_entity_id", sa.String(length=500), nullable=True),
        sa.Column("sso_url", sa.String(length=500), nullable=True),
        sa.Column("slo_url", sa.String(length=500), nullable=True),
        sa.Column("x509_cert", sa.Text(), nullable=True),
        sa.Column("certificate_expires_at", sa.DateTime(timezone=True), nullable=True),
        # OAuth/OIDC fields
        sa.Column("client_id", sa.String(length=500), nullable=True),
        sa.Column("client_secret", sa.String(length=500), nullable=True),
        sa.Column("authorization_endpoint", sa.String(length=500), nullable=True),
        sa.Column("token_endpoint", sa.String(length=500), nullable=True),
        sa.Column("userinfo_endpoint", sa.String(length=500), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        # Configuration
        sa.Column("attribute_mapping", sa.JSON(), nullable=True),
        sa.Column("role_mapping", sa.JSON(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("jit_enabled", sa.Boolean(), nullable=True, server_default="1"),
        sa.Column("auto_assign_roles", sa.Boolean(), nullable=True, server_default="1"),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sso_configs_id"), "sso_configs", ["id"], unique=False)

    # Create sso_sessions table
    op.create_table(
        "sso_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("provider_session_id", sa.String(length=255), nullable=True),
        sa.Column("name_id", sa.String(length=500), nullable=True),
        sa.Column(
            "provider_type", sa.String(length=20), nullable=False
        ),  # 'SAML', 'OIDC', 'OAUTH'
        sa.Column("login_method", sa.String(length=50), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("logged_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sso_sessions_id"), "sso_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_sso_sessions_session_id"), "sso_sessions", ["session_id"], unique=True
    )
    op.create_index(
        op.f("ix_sso_sessions_user_id"), "sso_sessions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_sso_sessions_provider_session_id"),
        "sso_sessions",
        ["provider_session_id"],
        unique=False,
    )

    # Create sso_audit_logs table
    op.create_table(
        "sso_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_status", sa.String(length=20), nullable=True),
        sa.Column("provider_type", sa.String(length=20), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sso_audit_logs_id"), "sso_audit_logs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_sso_audit_logs_organization_id"),
        "sso_audit_logs",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sso_audit_logs_user_id"), "sso_audit_logs", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_sso_audit_logs_event_type"),
        "sso_audit_logs",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sso_audit_logs_created_at"),
        "sso_audit_logs",
        ["created_at"],
        unique=False,
    )

    # Add SSO fields to users table using batch_alter_table for SQLite
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("is_sso_user", sa.Boolean(), server_default="0", nullable=True)
        )
        batch_op.add_column(sa.Column("sso_external_id", sa.String(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_users_organization_id"), ["organization_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_users_sso_external_id"), ["sso_external_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_users_organization", "organizations", ["organization_id"], ["id"]
        )


def downgrade():
    # Remove foreign key and indexes from users
    op.drop_constraint("fk_users_organization", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_sso_external_id"), table_name="users")
    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_column("users", "sso_external_id")
    op.drop_column("users", "is_sso_user")
    op.drop_column("users", "organization_id")

    # Drop sso_audit_logs table
    op.drop_index(op.f("ix_sso_audit_logs_created_at"), table_name="sso_audit_logs")
    op.drop_index(op.f("ix_sso_audit_logs_event_type"), table_name="sso_audit_logs")
    op.drop_index(op.f("ix_sso_audit_logs_user_id"), table_name="sso_audit_logs")
    op.drop_index(
        op.f("ix_sso_audit_logs_organization_id"), table_name="sso_audit_logs"
    )
    op.drop_index(op.f("ix_sso_audit_logs_id"), table_name="sso_audit_logs")
    op.drop_table("sso_audit_logs")

    # Drop sso_sessions table
    op.drop_index(
        op.f("ix_sso_sessions_provider_session_id"), table_name="sso_sessions"
    )
    op.drop_index(op.f("ix_sso_sessions_user_id"), table_name="sso_sessions")
    op.drop_index(op.f("ix_sso_sessions_session_id"), table_name="sso_sessions")
    op.drop_index(op.f("ix_sso_sessions_id"), table_name="sso_sessions")
    op.drop_table("sso_sessions")

    # Drop sso_configs table
    op.drop_index(op.f("ix_sso_configs_id"), table_name="sso_configs")
    op.drop_table("sso_configs")

    # Drop organizations table
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_domain"), table_name="organizations")
    op.drop_table("organizations")

    # Drop enum type
    op.execute("DROP TYPE ssoprovidertype")
