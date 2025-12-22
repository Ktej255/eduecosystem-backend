"""Add translation models for i18n support

Revision ID: add_translation_models
Revises: [previous_revision]
Create Date: 2025-11-26 08:50:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_translation_models_v2"
down_revision = "3ed110f5f0da"  # Current head: orders and invoices
branch_labels = None
depends_on = None


def upgrade():
    # Create languages table
    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("native_name", sa.String(length=100), nullable=False),
        sa.Column("is_rtl", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("flag_emoji", sa.String(length=10), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_languages_code", "languages", ["code"], unique=True)
    op.create_index("ix_languages_id", "languages", ["id"], unique=False)

    # Create translations table
    op.create_table(
        "translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "namespace", sa.String(length=100), nullable=True, server_default="common"
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_html", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "key", "language_code", "namespace", name="uix_translation_key_lang_ns"
        ),
    )
    op.create_index("ix_translations_id", "translations", ["id"], unique=False)
    op.create_index("ix_translations_key", "translations", ["key"], unique=False)
    op.create_index(
        "ix_translations_language_code", "translations", ["language_code"], unique=False
    )
    op.create_index(
        "ix_translations_namespace", "translations", ["namespace"], unique=False
    )

    # Create content_translations table
    op.create_table(
        "content_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("translated_value", sa.Text(), nullable=False),
        sa.Column(
            "is_machine_translated", sa.Boolean(), nullable=True, server_default="false"
        ),
        sa.Column("translator_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "content_type",
            "content_id",
            "field_name",
            "language_code",
            name="uix_content_translation",
        ),
    )
    op.create_index(
        "ix_content_translations_content_type",
        "content_translations",
        ["content_type"],
        unique=False,
    )
    op.create_index(
        "ix_content_translations_content_id",
        "content_translations",
        ["content_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_translations_id", "content_translations", ["id"], unique=False
    )
    op.create_index(
        "ix_content_translations_language_code",
        "content_translations",
        ["language_code"],
        unique=False,
    )

    # Create user_language_preferences table
    op.create_table(
        "user_language_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "preferred_language",
            sa.String(length=10),
            nullable=False,
            server_default="en",
        ),
        sa.Column("content_languages", sa.String(length=255), nullable=True),
        sa.Column("auto_translate", sa.Boolean(), nullable=True, server_default="true"),
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
        "ix_user_language_preferences_id",
        "user_language_preferences",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_user_language_preferences_user_id",
        "user_language_preferences",
        ["user_id"],
        unique=True,
    )

    # Insert default languages
    op.execute("""
        INSERT INTO languages (code, name, native_name, is_rtl, flag_emoji, sort_order) VALUES
        ('en', 'English', 'English', 0, '🇺🇸', 0),
        ('es', 'Spanish', 'Español', 0, '🇪🇸', 1),
        ('fr', 'French', 'Français', 0, '🇫🇷', 2),
        ('de', 'German', 'Deutsch', 0, '🇩🇪', 3),
        ('ar', 'Arabic', 'العربية', 1, '🇸🇦', 4),
        ('hi', 'Hindi', 'हिन्दी', 0, '🇮🇳', 5),
        ('zh', 'Chinese', '中文', 0, '🇨🇳', 6),
        ('ja', 'Japanese', '日本語', 0, '🇯🇵', 7),
        ('ko', 'Korean', '한국어', 0, '🇰🇷', 8),
        ('pt', 'Portuguese', 'Português', 0, '🇵🇹', 9),
        ('ru', 'Russian', 'Русский', 0, '🇷🇺', 10),
        ('it', 'Italian', 'Italiano', 0, '🇮🇹', 11);
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table("user_language_preferences")
    op.drop_table("content_translations")
    op.drop_table("translations")
    op.drop_table("languages")
