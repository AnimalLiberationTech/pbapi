"""
Unit tests for PostgreSQL adapter.
Tests the PostgreSQL adapter's data handling, especially for auto-increment fields.
"""

from unittest.mock import Mock

import pytest

from src.adapters.db.postgresql import PostgreSQLAdapter
from src.schemas.common import TableName


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def adapter(mock_logger):
    """Create a PostgreSQL adapter instance for testing."""
    return PostgreSQLAdapter(mock_logger)


class TestPostgreSQLAdapterBuildInsertData:
    """Test the _build_insert_data method for proper handling of id fields."""

    def test_excludes_id_when_none(self, adapter):
        """Test that _build_insert_data excludes id when it's None."""
        adapter.current_table = TableName.SHOP

        # Test data with None id
        data = {
            "id": None,
            "country_code": "md",
            "company_id": "12345",
            "address": "Test Address",
            "osm_data": {"type": "node", "key": 123},
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # Assert that 'id' is NOT in the columns when it's None
        assert "id" not in columns, "id should not be in columns when it's None"
        assert len(columns) == len(values), "columns and values should have same length"
        assert len(columns) == len(
            placeholders
        ), "columns and placeholders should have same length"

        # Assert that other fields are present
        assert "country_code" in columns
        assert "company_id" in columns
        assert "address" in columns

    def test_includes_id_when_has_value(self, adapter):
        """Test that _build_insert_data includes id when it has a value."""
        adapter.current_table = TableName.SHOP

        # Test data with valid id
        data = {
            "id": 42,
            "country_code": "md",
            "company_id": "12345",
            "address": "Test Address",
            "osm_data": {"type": "node", "key": 123},
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # Assert that 'id' IS in the columns when it has a value
        assert "id" in columns, "id should be in columns when it has a value"
        assert 42 in values, "id value should be in values"

    def test_excludes_id_when_key_missing(self, adapter):
        """Test that _build_insert_data works when id key is missing entirely."""
        adapter.current_table = TableName.SHOP

        # Test data without id key
        data = {
            "country_code": "md",
            "company_id": "12345",
            "address": "Test Address",
            "osm_data": {"type": "node", "key": 123},
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # Assert that 'id' is NOT in the columns
        assert "id" not in columns, "id should not be in columns when key is missing"

    def test_handles_receipt_with_none_id(self, adapter):
        """Test handling of receipt data with None id."""
        adapter.current_table = TableName.RECEIPT

        data = {
            "id": None,
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "date": "2026-02-20T10:00:00Z",
            "company_id": "123",
            "company_name": "Test Company",
            "country_code": "md",
            "cash_register_id": "CR1",
            "key": "42",
            "currency_code": "mdl",
            "total_amount": 100.50,
            "receipt_url": "https://example.com/receipt/42",
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # id should not be in columns when None
        assert "id" not in columns

    def test_handles_receipt_with_string_id(self, adapter):
        """Test handling of receipt data with string id."""
        adapter.current_table = TableName.RECEIPT

        data = {
            "id": "md_cr_1_42",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "date": "2026-02-20T10:00:00Z",
            "company_id": "123",
            "company_name": "Test Company",
            "country_code": "md",
            "cash_register_id": "CR1",
            "key": "42",
            "currency_code": "mdl",
            "total_amount": 100.50,
            "receipt_url": "https://example.com/receipt/42",
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # id should be in columns when it has a value
        assert "id" in columns
        assert "md_cr_1_42" in values

    def test_handles_shop_item_with_uuid_id(self, adapter):
        """Test handling of shop_item data with UUID id."""
        adapter.current_table = TableName.SHOP_ITEM

        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "shop_id": 42,
            "name": "Test Item",
            "status": "pending",
            "barcode": None,
        }

        columns, placeholders, values = adapter._build_insert_data(data)

        # id should be in columns when it has a value
        assert "id" in columns
        assert "123e4567-e89b-12d3-a456-426614174000" in values
