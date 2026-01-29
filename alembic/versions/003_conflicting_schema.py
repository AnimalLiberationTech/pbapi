"""Conflicting tables - shop, user, and related tables

Revision ID: 003_conflicting_schema
Revises: 002_shop_address
Create Date: 2026-01-04

This migration creates tables that CONFLICT with legacy schema names.
These are new tables with different structure from legacy shop/user tables.
The new tables use prefixed names to avoid conflicts:
- rp_shop (receipt-parser shop)
- rp_user
- rp_user_identity
- rp_user_session
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "003_conflicting_schema"
down_revision: Union[str, None] = "002_shop_address"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Create conflicting tables with rp_ prefix."""
    sql_file = get_sql_file_path("003_conflicting_schema_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Drop conflicting tables."""
    sql_file = get_sql_file_path("003_conflicting_schema_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)
