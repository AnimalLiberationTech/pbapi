"""Rename purchased_item.quantity_unit to unit and add unit_quantity

Revision ID: 005_purchased_item_unit
Revises: 004_add_identity_providers
Create Date: 2026-02-11

"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "005_purchased_item_unit"
down_revision: Union[str, None] = "004_add_identity_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Rename column and add unit_quantity column."""
    sql_file = get_sql_file_path("005_purchased_item_unit_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Revert rename and remove unit_quantity column."""
    sql_file = get_sql_file_path("005_purchased_item_unit_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)
