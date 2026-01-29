"""Add new values to identity_provider enum

Revision ID: 004_add_identity_providers
Revises: 003_conflicting_schema
Create Date: 2026-01-29

"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
# pylint: disable=C0103
revision: str = "004_add_identity_providers"
down_revision: Union[str, None] = "003_conflicting_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# pylint: enable=C0103


def get_sql_file_path(filename: str) -> str:
    """Get the full path to a SQL file in the versions' directory."""
    return os.path.join(os.path.dirname(__file__), filename)


def upgrade() -> None:
    """Add telegram, appwrite, supabase to identity_provider enum."""
    sql_file = get_sql_file_path("004_add_identity_providers_up.sql")
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # ALTER TYPE ... ADD VALUE cannot be executed in a transaction block
    # We must end the current transaction if one is active.
    # However, Alembic usually wraps migrations in a transaction.
    # We can use op.get_bind().execute() with autocommit if needed,
    # or rely on context.configure(autocommit_block=True) if supported.
    # A common way in Alembic to handle this is:
    op.execute("COMMIT")
    for command in sql.split(";"):
        if command.strip():
            op.execute(command.strip())


def downgrade() -> None:
    """Removing enum values is not supported by PostgreSQL."""
    pass
