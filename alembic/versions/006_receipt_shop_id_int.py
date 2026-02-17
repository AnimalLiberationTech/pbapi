"""Change receipt.shop_id from UUID to INTEGER

Revision ID: 006_receipt_shop_id_int
Revises: 005_purchased_item_unit
Create Date: 2026-02-17

"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "006_receipt_shop_id_int"
down_revision: Union[str, None] = "005_purchased_item_unit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Change shop_id to integer."""
    sql_file = get_sql_file_path("006_receipt_shop_id_int_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Revert shop_id to UUID."""
    sql_file = get_sql_file_path("006_receipt_shop_id_int_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)
