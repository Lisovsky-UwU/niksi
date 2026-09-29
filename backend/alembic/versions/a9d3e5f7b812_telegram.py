"""telegram bot

Revision ID: a9d3e5f7b812
Revises: f2c8a4d17e65
Create Date: 2026-09-30 18:00:00

Links people to their Telegram accounts (through a one-time code from the web settings)
and remembers the couple's shared chat where the bot answers, notifies and sums up.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a9d3e5f7b812"
down_revision: Union[str, Sequence[str], None] = "f2c8a4d17e65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_user_id", sa.BigInteger(), nullable=True))
    op.create_unique_constraint("uq_users_telegram_user_id", "users", ["telegram_user_id"])
    op.add_column("users", sa.Column("telegram_link_code", sa.String(length=12), nullable=True))
    op.add_column("users", sa.Column("telegram_link_code_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "telegram_chats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("bound_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notify_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("daily_summary_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_summary_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.UniqueConstraint("chat_id", name="uq_telegram_chats_chat_id"),
    )


def downgrade() -> None:
    op.drop_table("telegram_chats")
    op.drop_column("users", "telegram_link_code_expires_at")
    op.drop_column("users", "telegram_link_code")
    op.drop_constraint("uq_users_telegram_user_id", "users", type_="unique")
    op.drop_column("users", "telegram_user_id")
