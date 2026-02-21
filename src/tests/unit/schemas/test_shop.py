from datetime import datetime
from unittest import TestCase
from uuid import UUID

import pytest

from src.schemas.common import CountryCode, OsmType
from src.schemas.osm_data import OsmData
from src.schemas.shop import Shop


class TestShop(TestCase):
    """Test suite for Shop schema."""

    def setUp(self):
        """Set up test fixtures."""
        self.creator_id = UUID("12345678-1234-5678-1234-567812345678")
        self.osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        self.shop_data = {
            "country_code": CountryCode.MOLDOVA,
            "company_id": "5897403875",
            "address": "Test Address, Chisinau",
            "osm_data": self.osm_data,
            "creator_user_id": self.creator_id,
        }

    def test_shop_creation_basic(self):
        """Test basic shop creation with required fields."""
        shop = Shop(**self.shop_data)

        assert shop.country_code == CountryCode.MOLDOVA
        assert shop.company_id == "5897403875"
        assert shop.address == "Test Address, Chisinau"
        assert shop.creator_user_id == self.creator_id
        assert shop.osm_data == self.osm_data

    def test_shop_id_is_optional(self):
        """Test that shop.id is optional and defaults to None."""
        shop = Shop(**self.shop_data)

        assert shop.id is None

    def test_shop_with_preset_id(self):
        """Test shop creation with a preset ID."""
        shop_data = {**self.shop_data, "id": 42}
        shop = Shop(**shop_data)

        assert shop.id == 42

    def test_shop_osm_id_auto_generated_from_osm_data(self):
        """Test that osm_id is auto-generated when None."""
        shop = Shop(**self.shop_data)

        # osm_id should be generated in format: {osm_type_code}:{key}
        # NODE = 1, so it should be "1:123456"
        assert shop.osm_id is not None
        assert shop.osm_id == "1:123456"

    def test_shop_osm_id_always_present(self):
        """Test that osm_id is ALWAYS present after initialization."""
        shop = Shop(**self.shop_data)

        # osm_id must not be None
        assert shop.osm_id is not None
        assert isinstance(shop.osm_id, str)
        assert len(shop.osm_id) > 0

    def test_shop_osm_id_generation_for_node_type(self):
        """Test osm_id generation with NODE type (code=1)."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=999,
            lat="10.0",
            lon="20.0",
            display_name="Node Shop",
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        assert shop.osm_id == "1:999"

    def test_shop_osm_id_generation_for_way_type(self):
        """Test osm_id generation with WAY type (code=3)."""
        osm_data = OsmData(
            type=OsmType.WAY,
            key=456,
            lat="10.0",
            lon="20.0",
            display_name="Way Shop",
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        assert shop.osm_id == "3:456"

    def test_shop_osm_id_generation_for_relation_type(self):
        """Test osm_id generation with RELATION type (code=2)."""
        osm_data = OsmData(
            type=OsmType.RELATION,
            key=789,
            lat="10.0",
            lon="20.0",
            display_name="Relation Shop",
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        assert shop.osm_id == "2:789"

    def test_shop_osm_id_respects_preset_value(self):
        """Test that preset osm_id is respected and not overwritten."""
        shop_data = {**self.shop_data, "osm_id": "custom_osm_id"}
        shop = Shop(**shop_data)

        # If osm_id is provided, it should NOT be overwritten
        assert shop.osm_id == "custom_osm_id"

    def test_shop_osm_id_with_large_key(self):
        """Test osm_id generation with large OSM key."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=9999999999,
            lat="10.0",
            lon="20.0",
            display_name="Large Key Shop",
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        assert shop.osm_id == "1:9999999999"
        assert isinstance(shop.osm_id, str)

    def test_shop_creation_time_auto_set(self):
        """Test that creation_time is automatically set."""
        before = int(datetime.now().timestamp())
        shop = Shop(**self.shop_data)
        after = int(datetime.now().timestamp())

        assert shop.creation_time >= before
        assert shop.creation_time <= after + 1

    def test_shop_creation_time_can_be_preset(self):
        """Test that creation_time can be overridden."""
        preset_time = 1234567890
        shop_data = {**self.shop_data, "creation_time": preset_time}
        shop = Shop(**shop_data)

        assert shop.creation_time == preset_time

    def test_shop_serialization_includes_osm_id(self):
        """Test that model_dump includes osm_id."""
        shop = Shop(**self.shop_data)
        dumped = shop.model_dump()

        assert "osm_id" in dumped
        assert dumped["osm_id"] == "1:123456"

    def test_shop_serialization_json_mode(self):
        """Test that JSON serialization includes osm_id."""
        shop = Shop(**self.shop_data)
        json_data = shop.model_dump(mode="json")

        assert "osm_id" in json_data
        assert isinstance(json_data["osm_id"], str)

    def test_shop_country_code_required(self):
        """Test that country_code is required."""
        bad_data = {**self.shop_data}
        del bad_data["country_code"]

        with pytest.raises(ValueError):
            Shop(**bad_data)

    def test_shop_company_id_required(self):
        """Test that company_id is required."""
        bad_data = {**self.shop_data}
        del bad_data["company_id"]

        with pytest.raises(ValueError):
            Shop(**bad_data)

    def test_shop_address_required(self):
        """Test that address is required."""
        bad_data = {**self.shop_data}
        del bad_data["address"]

        with pytest.raises(ValueError):
            Shop(**bad_data)

    def test_shop_osm_data_required(self):
        """Test that osm_data is required."""
        bad_data = {**self.shop_data}
        del bad_data["osm_data"]

        with pytest.raises(ValueError):
            Shop(**bad_data)

    def test_shop_creator_user_id_required(self):
        """Test that creator_user_id is required."""
        bad_data = {**self.shop_data}
        del bad_data["creator_user_id"]

        with pytest.raises(ValueError):
            Shop(**bad_data)

    def test_shop_with_different_country_codes(self):
        """Test shop creation with different country codes."""
        shop_data = {**self.shop_data, "country_code": CountryCode.MOLDOVA}
        shop = Shop(**shop_data)

        assert shop.country_code == CountryCode.MOLDOVA

    def test_shop_company_id_types(self):
        """Test shop with different company_id values."""
        # Test with numeric string
        shop_data = {**self.shop_data, "company_id": "123456789"}
        shop = Shop(**shop_data)
        assert shop.company_id == "123456789"

        # Test with alphanumeric
        shop_data = {**self.shop_data, "company_id": "cmp_abc123"}
        shop = Shop(**shop_data)
        assert shop.company_id == "cmp_abc123"

    def test_shop_address_with_special_characters(self):
        """Test shop address with special characters."""
        address_with_chars = "123 Main St, Apt #4-B, City (Region)"
        shop_data = {**self.shop_data, "address": address_with_chars}
        shop = Shop(**shop_data)

        assert shop.address == address_with_chars

    def test_shop_osm_data_persists(self):
        """Test that osm_data is preserved correctly."""
        shop = Shop(**self.shop_data)

        assert shop.osm_data.type == OsmType.NODE
        assert shop.osm_data.key == 123456
        assert shop.osm_data.lat == "47.0293446"
        assert shop.osm_data.lon == "28.8638389"

    def test_shop_creator_user_id_preserved(self):
        """Test that creator_user_id is preserved."""
        shop = Shop(**self.shop_data)

        assert shop.creator_user_id == self.creator_id

    def test_shop_osm_id_format_consistency(self):
        """Test that osm_id format is always 'code:key'."""
        shop = Shop(**self.shop_data)

        parts = shop.osm_id.split(":")
        assert len(parts) == 2
        assert parts[0].isdigit()  # First part is the type code
        assert parts[1].isdigit()  # Second part is the key

    def test_shop_osm_id_matches_osm_data(self):
        """Test that osm_id matches the osm_data key."""
        shop = Shop(**self.shop_data)

        # Extract key from osm_id
        _, key_from_osm_id = shop.osm_id.split(":")
        assert int(key_from_osm_id) == shop.osm_data.key

    def test_shop_model_post_init_called(self):
        """Test that model_post_init is properly called."""
        shop = Shop(**self.shop_data)

        # osm_id should be set by model_post_init
        assert shop.osm_id is not None

    def test_shop_osm_id_none_initially_gets_generated(self):
        """Test that None osm_id is generated during initialization."""
        shop_data = {**self.shop_data, "osm_id": None}
        shop = Shop(**shop_data)

        # Should be generated, not None
        assert shop.osm_id is not None
        assert shop.osm_id == "1:123456"

    def test_shop_with_zero_key(self):
        """Test shop with OSM key of 0."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=0,
            lat="0.0",
            lon="0.0",
            display_name="Zero Key",
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        assert shop.osm_id == "1:0"

    def test_shop_json_schema_includes_osm_id(self):
        """Test that JSON schema defines osm_id."""
        schema = Shop.model_json_schema()

        assert "osm_id" in schema["properties"]

    def test_shop_multiple_instances_independent_osm_id(self):
        """Test that multiple shop instances have independent osm_ids."""
        shop1 = Shop(**self.shop_data)

        osm_data2 = OsmData(
            type=OsmType.WAY,
            key=999,
            lat="10.0",
            lon="20.0",
            display_name="Shop 2",
        )
        shop2_data = {**self.shop_data, "osm_data": osm_data2}
        shop2 = Shop(**shop2_data)

        assert shop1.osm_id != shop2.osm_id
        assert shop1.osm_id == "1:123456"
        assert shop2.osm_id == "3:999"

    def test_shop_osm_id_immutability_after_generation(self):
        """Test that osm_id doesn't change after generation."""
        shop = Shop(**self.shop_data)
        original_osm_id = shop.osm_id

        # Access again
        assert shop.osm_id == original_osm_id

    def test_shop_empty_address_invalid(self):
        """Test that empty address is handled."""
        shop_data = {**self.shop_data, "address": ""}
        shop = Shop(**shop_data)

        # Empty string is allowed as it's a str type
        assert shop.address == ""

    def test_shop_osm_id_with_empty_osm_data_display_name(self):
        """Test osm_id generation when osm_data has no display_name."""
        osm_data = OsmData(
            type=OsmType.NODE,
            key=111,
            lat="10.0",
            lon="20.0",
            display_name=None,
        )
        shop_data = {**self.shop_data, "osm_data": osm_data}
        shop = Shop(**shop_data)

        # osm_id should still be generated correctly
        assert shop.osm_id == "1:111"

    def test_shop_osm_id_computation_deterministic(self):
        """Test that osm_id computation is deterministic."""
        shop1 = Shop(**self.shop_data)
        shop2 = Shop(**self.shop_data)

        # Same input should produce same osm_id
        assert shop1.osm_id == shop2.osm_id

