"""Add address field to shop table

Revision ID: 002_shop_address
Revises: 001_initial_schema
Create Date: 2026-01-05
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "002_shop_address"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def upgrade() -> None:
    """Add address column to shop table."""
    op.execute("ALTER TABLE shop ADD COLUMN IF NOT EXISTS address TEXT DEFAULT NULL")
    op.execute("ALTER TABLE shop ADD COLUMN IF NOT EXISTS company_id TEXT DEFAULT NULL")
    op.execute("ALTER TABLE shop ADD COLUMN IF NOT EXISTS country_code country_code")


def downgrade() -> None:
    """Remove address column from shop table."""
    op.execute("ALTER TABLE shop DROP COLUMN IF EXISTS address")
