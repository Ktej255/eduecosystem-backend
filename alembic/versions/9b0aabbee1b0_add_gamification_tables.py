"""add_gamification_tables

Revision ID: 9b0aabbee1b0
Revises: 69e403a39700
Create Date: 2025-11-25 15:37:38.863129

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9b0aabbee1b0"
down_revision: Union[str, Sequence[str], None] = "69e403a39700"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add gamification tables."""

    # Create achievements table
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("rarity", sa.String(length=20), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("coin_reward", sa.Integer(), nullable=True),
        sa.Column("unlock_condition", sa.JSON(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_achievements_id"), "achievements", ["id"], unique=False)
    op.create_index(
        op.f("ix_achievements_name"), "achievements", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_achievements_category"), "achievements", ["category"], unique=False
    )

    # Create user_achievements table
    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column(
            "unlocked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("notified", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["achievement_id"], ["achievements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_achievements_id"), "user_achievements", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_user_achievements_user_id"),
        "user_achievements",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_achievements_achievement_id"),
        "user_achievements",
        ["achievement_id"],
        unique=False,
    )

    # Create challenges table
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("requirement", sa.JSON(), nullable=False),
        sa.Column("reward_coins", sa.Integer(), nullable=True),
        sa.Column("reward_achievement_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["reward_achievement_id"], ["achievements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_challenges_id"), "challenges", ["id"], unique=False)
    op.create_index(op.f("ix_challenges_type"), "challenges", ["type"], unique=False)
    op.create_index(
        op.f("ix_challenges_start_date"), "challenges", ["start_date"], unique=False
    )
    op.create_index(
        op.f("ix_challenges_end_date"), "challenges", ["end_date"], unique=False
    )

    # Create user_challenges table
    op.create_table(
        "user_challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("challenge_id", sa.Integer(), nullable=False),
        sa.Column("progress_data", sa.JSON(), nullable=True),
        sa.Column("progress_percentage", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reward_claimed", sa.Boolean(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["challenge_id"], ["challenges.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_challenges_id"), "user_challenges", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_user_challenges_user_id"), "user_challenges", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_challenges_challenge_id"),
        "user_challenges",
        ["challenge_id"],
        unique=False,
    )

    # Create coin_transactions table
    op.create_table(
        "coin_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_coin_transactions_id"), "coin_transactions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_coin_transactions_user_id"),
        "coin_transactions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_coin_transactions_type"), "coin_transactions", ["type"], unique=False
    )
    op.create_index(
        op.f("ix_coin_transactions_created_at"),
        "coin_transactions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - Remove gamification tables."""
    op.drop_index(
        op.f("ix_coin_transactions_created_at"), table_name="coin_transactions"
    )
    op.drop_index(op.f("ix_coin_transactions_type"), table_name="coin_transactions")
    op.drop_index(op.f("ix_coin_transactions_user_id"), table_name="coin_transactions")
    op.drop_index(op.f("ix_coin_transactions_id"), table_name="coin_transactions")
    op.drop_table("coin_transactions")

    op.drop_index(op.f("ix_user_challenges_challenge_id"), table_name="user_challenges")
    op.drop_index(op.f("ix_user_challenges_user_id"), table_name="user_challenges")
    op.drop_index(op.f("ix_user_challenges_id"), table_name="user_challenges")
    op.drop_table("user_challenges")

    op.drop_index(op.f("ix_challenges_end_date"), table_name="challenges")
    op.drop_index(op.f("ix_challenges_start_date"), table_name="challenges")
    op.drop_index(op.f("ix_challenges_type"), table_name="challenges")
    op.drop_index(op.f("ix_challenges_id"), table_name="challenges")
    op.drop_table("challenges")

    op.drop_index(
        op.f("ix_user_achievements_achievement_id"), table_name="user_achievements"
    )
    op.drop_index(op.f("ix_user_achievements_user_id"), table_name="user_achievements")
    op.drop_index(op.f("ix_user_achievements_id"), table_name="user_achievements")
    op.drop_table("user_achievements")

    op.drop_index(op.f("ix_achievements_category"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_name"), table_name="achievements")
    op.drop_index(op.f("ix_achievements_id"), table_name="achievements")
    op.drop_table("achievements")
