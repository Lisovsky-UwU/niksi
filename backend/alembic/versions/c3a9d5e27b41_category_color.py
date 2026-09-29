"""category colour

Revision ID: c3a9d5e27b41
Revises: b7e2c91f4a10
Create Date: 2026-09-29 18:00:00

A category may be marked with one of the coloured pencils; NULL keeps the automatic
colour picked by the category's position.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3a9d5e27b41"
down_revision: Union[str, Sequence[str], None] = "b7e2c91f4a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("color", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "color")
