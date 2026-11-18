"""Store hidden recent items per shopping list.

Revision ID: 8ac21d9e5f64
Revises: c2e936c8ab31
Create Date: 2026-11-18

"""

from alembic import op
import sqlalchemy as sa


revision = "8ac21d9e5f64"
down_revision = "c2e936c8ab31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shoppinglist_recent_item_hidden",
        sa.Column("shoppinglist_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["item_id"], ["item.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["shoppinglist_id"], ["shoppinglist.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("shoppinglist_id", "item_id"),
    )


def downgrade():
    op.drop_table("shoppinglist_recent_item_hidden")
