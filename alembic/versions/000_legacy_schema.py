"""Legacy schema from Plante database

Revision ID: 000_legacy_schema
Revises:
Create Date: 2026-01-03

This migration represents the existing Plante database schema.
It was extracted from a pg_dump backup of the dev database.
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "000_legacy_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Create legacy Plante database schema."""
    sql_file = get_sql_file_path("000_legacy_schema_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Drop legacy schema - WARNING: This will delete all legacy tables!"""
    sql_file = get_sql_file_path("000_legacy_schema_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)
