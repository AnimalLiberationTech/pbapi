"""Fix user_identity unique constraint to use (id, provider) composite

Revision ID: 007_fix_user_identity_pkey
Revises: 006_receipt_shop_id_int
Create Date: 2026-02-17

"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "007_fix_user_identity_pkey"
down_revision: Union[str, None] = "006_receipt_shop_id_int"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Fix user_identity unique constraint to use (id, provider) composite."""
    sql_file = get_sql_file_path("007_fix_user_identity_pkey_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)


def downgrade() -> None:
    """Revert user_identity constraint to use id as PRIMARY KEY."""
    sql_file = get_sql_file_path("007_fix_user_identity_pkey_down.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()
    op.execute(sql)

