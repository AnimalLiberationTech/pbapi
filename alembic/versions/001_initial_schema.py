"""Initial schema - create all tables

Revision ID: 001_initial_schema
Revises: 000_legacy_schema
Create Date: 2026-01-03

"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "001_initial_schema"
down_revision: Union[str, None] = "000_legacy_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Create all tables with proper schema based on src/schemas definitions."""
    sql_file = get_sql_file_path("001_initial_schema_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Drop all tables and types."""
    sql_file = get_sql_file_path("001_initial_schema_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)
