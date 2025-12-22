"""Add blockchain tables

Revision ID: add_blockchain
Revises: add_social_features
Create Date: 2025-11-22

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_blockchain"
down_revision = "add_social_features"
branch_labels = None
depends_on = None


def upgrade():
    # Create blockchain_blocks table
    op.create_table(
        "blockchain_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("previous_hash", sa.String(), nullable=False),
        sa.Column("hash", sa.String(), nullable=False),
        sa.Column("nonce", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_blockchain_blocks_hash"), "blockchain_blocks", ["hash"], unique=True
    )
    op.create_index(
        op.f("ix_blockchain_blocks_id"), "blockchain_blocks", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_blockchain_blocks_index"), "blockchain_blocks", ["index"], unique=True
    )

    # Add blockchain_hash column to certificates table
    op.add_column(
        "certificates", sa.Column("blockchain_hash", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_certificates_blockchain_hash"),
        "certificates",
        ["blockchain_hash"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix_certificates_blockchain_hash"), table_name="certificates")
    op.drop_column("certificates", "blockchain_hash")
    op.drop_index(op.f("ix_blockchain_blocks_index"), table_name="blockchain_blocks")
    op.drop_index(op.f("ix_blockchain_blocks_id"), table_name="blockchain_blocks")
    op.drop_index(op.f("ix_blockchain_blocks_hash"), table_name="blockchain_blocks")
    op.drop_table("blockchain_blocks")
