import os
import uuid
from typing import Any, Dict, List, Self

from psycopg2 import connect
from psycopg2.extras import RealDictCursor, Json

from src.adapters.db.base import BaseDBAdapter
from src.schemas.common import TableName

# Define the relational columns for each table (excluding id, data, created_at, updated_at)
TABLE_COLUMNS = {
    TableName.RECEIPT: [
        "user_id",
        "date",
        "company_id",
        "company_name",
        "country_code",
        "cash_register_id",
        "key",
        "currency_code",
        "total_amount",
        "receipt_url",
        "shop_id",
    ],
    TableName.RECEIPT_URL: ["url", "receipt_id"],
    TableName.PURCHASED_ITEM: [
        "receipt_id",
        "name",
        "quantity",
        "unit",
        "unit_quantity",
        "price",
        "item_id",
    ],
    TableName.SHOP_ITEM: ["shop_id", "name", "status", "barcode"],
    TableName.SHOP: ["country_code", "company_id", "address", "osm_data"],
    TableName.USER: [
        "email",
        "name",
        "login_generation",
        "banned",
        "self_description",
        "gender",
        "birthday",
        "user_rights_group",
        "avatar_id",
        "creation_time",
    ],
    TableName.USER_IDENTITY: ["provider", "user_id"],
    TableName.USER_SESSION: ["identity_provider", "user_id", "user_name", "state"],
}

# Tables that have the 'data' JSONB column for extra fields
TABLES_WITH_DATA_COLUMN = {
    TableName.RECEIPT,
    TableName.SHOP,
    TableName.USER,
}


class PostgreSQLAdapter(BaseDBAdapter):
    def __init__(self, logger):
        super().__init__(logger)
        self.connection = connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            database=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        )
        self.connection.autocommit = True
        self.current_table = None
        self.current_db = None

    def use_db(self, db_name: str) -> Self:
        self.current_db = db_name
        return self

    def use_table(self, table_name: TableName) -> Self:
        self.current_table = table_name
        return self

    def _get_table_columns(self) -> List[str]:
        """Get the relational columns for the current table."""
        return TABLE_COLUMNS.get(self.current_table, [])

    def _has_data_column(self) -> bool:
        """Check if the current table has a data JSONB column."""
        return self.current_table in TABLES_WITH_DATA_COLUMN

    def _build_insert_data(self, data: Dict[str, Any]) -> tuple:
        """Build column names, placeholders, and values for INSERT."""
        columns = ["id"]
        values = [data.get("id")]
        placeholders = ["%s"]

        table_columns = self._get_table_columns()
        extra_data = {}

        for key, value in data.items():
            if key == "id":
                continue
            if key in table_columns:
                columns.append(key)
                # Handle special types
                if isinstance(value, dict):
                    values.append(Json(value))
                else:
                    values.append(value)
                placeholders.append("%s")
            elif self._has_data_column():
                # Store non-column fields in data JSONB only if table has data column
                extra_data[key] = value

        # Include data column only for tables that have it
        if self._has_data_column():
            columns.append("data")
            values.append(Json(extra_data))
            placeholders.append("%s")

        return columns, placeholders, values

    def create_one(self, data: Dict[str, Any]) -> str:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        _id = data.get("id")
        if not _id:
            _id = str(uuid.uuid4())
            data["id"] = _id

        columns, placeholders, values = self._build_insert_data(data)

        with self.connection.cursor() as cursor:
            query = (
                f'INSERT INTO "{self.current_table}" ({", ".join(columns)}) '
                f"VALUES ({', '.join(placeholders)}) "
                "ON CONFLICT (id) DO NOTHING RETURNING id"
            )
            cursor.execute(query, values)
            result = cursor.fetchone()
            return result[0] if result else _id

    def create_or_update_one(self, data: Dict[str, Any]) -> bool:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        _id = data.get("id")
        if not _id:
            raise ValueError("ID is required for create_or_update_one")

        columns, placeholders, values = self._build_insert_data(data)

        # Build UPDATE SET clause (exclude id)
        update_cols = [c for c in columns if c != "id"]
        update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])

        with self.connection.cursor() as cursor:
            query = f"""
                INSERT INTO "{self.current_table}" ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id)
                DO UPDATE SET {update_set}
            """
            cursor.execute(query, values)
            return True

    def read_one(self, _id: str, **kwargs) -> Dict[str, Any] | None:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = f'SELECT * FROM "{self.current_table}" WHERE id = %s'
            cursor.execute(query, (_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a flat dictionary, merging data JSONB."""
        result = {}
        extra_data = {}

        for key, value in row.items():
            if key in ("created_at", "updated_at"):
                continue
            if key == "data" and self._has_data_column():
                extra_data = value if value else {}
            else:
                result[key] = value

        # Merge extra data from JSONB column
        result.update(extra_data)
        return result

    def read_many(
        self, where: Dict[str, Any] | None = None, limit: int | None = None, **kwargs
    ) -> List[Dict[str, Any]]:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        query = f'SELECT * FROM "{self.current_table}"'
        params = []

        if where:
            conditions = []
            table_columns = self._get_table_columns() + ["id"]
            for key, value in where.items():
                if key in table_columns:
                    conditions.append(f"{key} = %s")
                    params.append(value)
                elif self._has_data_column():
                    # Query JSONB field only for tables that have it
                    conditions.append(f"data->>%s = %s")
                    params.extend([key, str(value)])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def update_one(self, _id: str, data: Dict[str, Any]) -> bool:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        table_columns = self._get_table_columns()
        set_parts = []
        values = []
        extra_data = {}

        for key, value in data.items():
            if key == "id":
                continue
            if key in table_columns:
                set_parts.append(f"{key} = %s")
                if isinstance(value, dict):
                    values.append(Json(value))
                else:
                    values.append(value)
            elif self._has_data_column():
                extra_data[key] = value

        # Update data JSONB column only for tables that have it
        if self._has_data_column():
            set_parts.append("data = %s")
            values.append(Json(extra_data))

        if not set_parts:
            return False

        values.append(_id)

        with self.connection.cursor() as cursor:
            query = f'UPDATE "{self.current_table}" SET {", ".join(set_parts)} WHERE id = %s'
            cursor.execute(query, values)
            return cursor.rowcount > 0

    def delete_one(self, _id: str, **kwargs) -> bool:
        if not self.current_table:
            raise ValueError("Table not selected. Use use_table() first.")

        with self.connection.cursor() as cursor:
            query = f'DELETE FROM "{self.current_table}" WHERE id = %s'
            cursor.execute(query, (_id,))
            return cursor.rowcount > 0

    def create_table(self, table_name: TableName, **kwargs) -> Self:
        """Create a table with id and jsonb data column, plus a GIN index."""
        with self.connection.cursor() as cursor:
            query = f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    id TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            cursor.execute(query)

            index_query = f"""
                CREATE INDEX IF NOT EXISTS "idx_{table_name}_data"
                ON "{table_name}" USING GIN (data)
            """
            cursor.execute(index_query)

            self.logger.info(f"Table '{table_name}' created or already exists")
        return self

    def drop_table(self, table_name: TableName) -> None:
        with self.connection.cursor() as cursor:
            query = f'DROP TABLE IF EXISTS "{self.current_table}"'
            cursor.execute(query)


def init_db_session(logger) -> PostgreSQLAdapter:
    db_name = os.environ["POSTGRES_DB"]
    return PostgreSQLAdapter(logger).use_db(db_name)
