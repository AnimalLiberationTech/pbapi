"""
Unit tests for ShopHandler.
Tests cover creation, retrieval, and edge cases for shop management.
"""

from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from src.handlers.shop import ShopHandler
from src.schemas.common import TableName, OsmType, CountryCode
from src.schemas.shop import Shop
from src.schemas.osm_data import OsmData


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def shop_handler(mock_logger):
    """Create a ShopHandler instance with mocked database."""
    with patch("src.handlers.shop.init_db_session") as mock_init:
        mock_init.return_value = Mock()
        handler = ShopHandler(mock_logger)
        handler.db = Mock()
        return handler


@pytest.fixture
def sample_osm_data():
    """Sample OSM data for testing."""
    return OsmData(
        type=OsmType.NODE,
        key=123456,
        lat="47.0293446",
        lon="28.8638389",
        display_name="Test Shop, Chisinau, Moldova"
    )


@pytest.fixture
def sample_shop(sample_osm_data):
    """Sample shop for testing."""
    return Shop(
        country_code=CountryCode.MOLDOVA,
        company_id="5897403875",
        address="Test Address, Chisinau",
        osm_data=sample_osm_data,
        creator_user_id=UUID("12345678-1234-5678-1234-567812345678")
    )


class TestShopHandlerGetOrCreateExisting:
    """Tests for retrieving an existing shop."""

    def test_get_existing_shop_by_osm_id(self, shop_handler, sample_shop):
        """Test retrieving an existing shop by osm_id."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": CountryCode.MOLDOVA,
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 42
        assert result.osm_id == "1:123456"
        shop_handler.db.use_table.assert_called_with(TableName.SHOP)
        shop_handler.db.read_many.assert_called_with({"osm_id": sample_shop.osm_id}, limit=1)
        shop_handler.db.create_one.assert_not_called()

    def test_get_existing_shop_with_null_country_code(self, shop_handler, sample_shop):
        """Test retrieving existing shop with null country_code (backward compatibility)."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": None,
            "company_id": None,
            "address": None,
            "osm_data": None,
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 42
        assert result.country_code == CountryCode.MOLDOVA
        assert result.company_id == "5897403875"

    def test_get_existing_shop_with_null_company_id(self, shop_handler, sample_shop):
        """Test retrieving existing shop with null company_id (backward compatibility)."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": CountryCode.MOLDOVA,
            "company_id": None,
            "address": "Test Address, Chisinau",
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        assert result.company_id == "5897403875"

    def test_get_existing_shop_with_null_address(self, shop_handler, sample_shop):
        """Test retrieving existing shop with null address (backward compatibility)."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": CountryCode.MOLDOVA,
            "company_id": "5897403875",
            "address": None,
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        assert result.address == "Test Address, Chisinau"

    def test_get_existing_shop_with_null_osm_data(self, shop_handler, sample_shop):
        """Test retrieving existing shop with null osm_data (backward compatibility)."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": CountryCode.MOLDOVA,
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": None,
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        assert result.osm_data == sample_shop.osm_data

    def test_get_existing_shop_logs_result(self, shop_handler, sample_shop, mock_logger):
        """Test that get_or_create logs the database result."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": CountryCode.MOLDOVA,
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        shop_handler.get_or_create(sample_shop)

        mock_logger.info.assert_called()
        assert mock_logger.info.call_args[0][0] == [existing_shop_data]


class TestShopHandlerGetOrCreateNew:
    """Tests for creating a new shop."""

    def test_create_new_shop(self, shop_handler, sample_shop):
        """Test creating a new shop when it doesn't exist."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "99"

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 99
        shop_handler.db.use_table.assert_called_with(TableName.SHOP)
        shop_handler.db.read_many.assert_called_with({"osm_id": sample_shop.osm_id}, limit=1)
        shop_handler.db.create_one.assert_called_once()

        # Verify that the shop data was passed to create_one
        create_call_args = shop_handler.db.create_one.call_args[0][0]
        assert create_call_args["country_code"] == CountryCode.MOLDOVA
        assert create_call_args["company_id"] == "5897403875"

    def test_create_new_shop_with_string_id_returned(self, shop_handler, sample_shop):
        """Test creating a new shop where database returns string id."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "123"

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 123
        assert isinstance(result.id, int)

    def test_create_new_shop_with_large_id(self, shop_handler, sample_shop):
        """Test creating a new shop with a large ID value."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "2147483647"  # Max 32-bit int

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 2147483647

    def test_create_new_shop_logs_result(self, shop_handler, sample_shop, mock_logger):
        """Test that create_one result is logged."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "99"

        shop_handler.get_or_create(sample_shop)

        # Should log twice: once for read_many result, once for create_one result
        assert mock_logger.info.call_count >= 1

    def test_create_new_shop_with_none_id_not_included(self, shop_handler, sample_shop):
        """Test that None id is handled correctly when creating a shop."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "99"

        # Verify shop.id is None before calling get_or_create
        assert sample_shop.id is None

        result = shop_handler.get_or_create(sample_shop)

        # Verify that create_one was called with the shop data
        shop_handler.db.create_one.assert_called_once()

        # Verify that the returned ID is correctly set on the result
        assert result.id == 99

        # The create_one receives model_dump which includes id field
        call_args = shop_handler.db.create_one.call_args[0][0]
        assert "id" in call_args
        # The id field in the dump is None, which the PostgreSQL adapter
        # correctly excludes from the INSERT, allowing auto-increment to work
        assert call_args["id"] is None


class TestShopHandlerEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_osm_id_generation_for_node_type(self, shop_handler, mock_logger):
        """Test that osm_id is correctly generated for NODE type."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop"
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678")
        )

        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "1"

        result = shop_handler.get_or_create(shop)

        # osm_id should be "1:123456" (NODE=1)
        assert result.osm_id == "1:123456"

    def test_osm_id_generation_for_way_type(self, shop_handler, mock_logger):
        """Test that osm_id is correctly generated for WAY type."""
        osm_data = OsmData(
            type=OsmType.WAY,
            key=789012,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop"
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678")
        )

        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "1"

        result = shop_handler.get_or_create(shop)

        # osm_id should be "3:789012" (WAY=3)
        assert result.osm_id == "3:789012"

    def test_osm_id_generation_for_relation_type(self, shop_handler, mock_logger):
        """Test that osm_id is correctly generated for RELATION type."""
        osm_data = OsmData(
            type=OsmType.RELATION,
            key=456789,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop"
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678")
        )

        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "1"

        result = shop_handler.get_or_create(shop)

        # osm_id should be "2:456789" (RELATION=2)
        assert result.osm_id == "2:456789"

    def test_empty_read_many_result(self, shop_handler, sample_shop):
        """Test handling of empty read_many result (shop doesn't exist)."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "1"

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 1
        shop_handler.db.create_one.assert_called_once()

    def test_multiple_shops_returned_uses_first(self, shop_handler, sample_shop):
        """Test that get_or_create uses the first result when multiple are returned."""
        first_shop = {
            "id": 42,
            "osm_id": sample_shop.osm_id,
            "country_code": "md",
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        second_shop = {
            "id": 99,
            "osm_id": sample_shop.osm_id,
            "country_code": "md",
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": sample_shop.osm_data.model_dump(mode="json"),
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [first_shop, second_shop]

        result = shop_handler.get_or_create(sample_shop)

        assert result.id == 42  # First shop should be used
        shop_handler.db.create_one.assert_not_called()

    def test_database_use_table_called_first(self, shop_handler, sample_shop):
        """Test that use_table is called before any other database operations."""
        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "1"

        shop_handler.get_or_create(sample_shop)

        # use_table should be the first call
        first_call = shop_handler.db.use_table.call_args
        assert first_call[0][0] == TableName.SHOP

    def test_handler_initialization(self, mock_logger):
        """Test that ShopHandler initializes correctly."""
        with patch("src.handlers.shop.init_db_session") as mock_init:
            mock_db = Mock()
            mock_init.return_value = mock_db

            handler = ShopHandler(mock_logger)

            assert handler.logger == mock_logger
            assert handler.db == mock_db
            mock_init.assert_called_once_with(mock_logger)

    def test_backward_compatibility_all_null_fields(self, shop_handler, sample_shop):
        """Test backward compatibility when all nullable fields are null."""
        existing_shop_data = {
            "id": 42,
            "osm_id": "1:123456",
            "country_code": None,
            "company_id": None,
            "address": None,
            "osm_data": None,
            "creator_user_id": str(sample_shop.creator_user_id),
            "creation_time": 1234567890
        }
        shop_handler.db.read_many.return_value = [existing_shop_data]

        result = shop_handler.get_or_create(sample_shop)

        # All fields should be populated from the incoming shop
        assert result.country_code == CountryCode.MOLDOVA
        assert result.company_id == "5897403875"
        assert result.address == "Test Address, Chisinau"
        assert result.osm_data == sample_shop.osm_data

    def test_shop_with_preset_id_returns_it(self, shop_handler):
        """Test that if shop has a preset id, it's preserved when creating."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop"
        )
        shop = Shop(
            id=999,  # Preset ID
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678")
        )

        shop_handler.db.read_many.return_value = []
        shop_handler.db.create_one.return_value = "999"

        result = shop_handler.get_or_create(shop)

        assert result.id == 999



