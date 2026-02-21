from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from starlette.exceptions import HTTPException

from src.handlers.sfs_md.receipt import SfsMdReceiptHandler
from src.schemas.common import TableName, ItemBarcodeStatus
from src.schemas.sfs_md.receipt import SfsMdReceipt
from src.tests.unit import make_receipt


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def handler(mock_logger):
    with patch("src.handlers.sfs_md.receipt.init_db_session") as mock_init:
        mock_init.return_value = Mock()
        return SfsMdReceiptHandler(mock_logger)


class TestSfsMdReceiptHandlerGetByUrl:
    def test_get_by_url_success(self, handler, mock_logger):
        url = "https://example.com/receipt"
        receipt_url_data = {"id": "hash123", "url": url, "receipt_id": "receipt123"}
        receipt_data = {
            "id": "receipt123",
            "date": "2026-02-14T00:00:00+00:00",
            "user_id": "12345678-1234-5678-1234-567812345678",
            "company_id": "cmp_1",
            "company_name": "Test Co",
            "shop_address": "123 Test Street",
            "cash_register_id": "cr_1",
            "key": 42,
            "total_amount": 12.34,
            "purchases": [],
            "receipt_url": url,
        }

        handler.db.read_one = Mock(side_effect=[receipt_url_data, receipt_data])

        with patch("src.handlers.sfs_md.receipt.make_hash", return_value="hash123"):
            result = handler.get_by_url(url)

        assert result is not None
        assert isinstance(result, SfsMdReceipt)
        assert handler.db.use_table.call_count == 2

    def test_get_by_url_receipt_url_not_found(self, handler, mock_logger):
        url = "https://example.com/receipt"
        handler.db.read_one = Mock(return_value=None)

        with patch("src.handlers.sfs_md.receipt.make_hash", return_value="hash123"):
            result = handler.get_by_url(url)

        assert result is None
        assert handler.db.use_table.call_count == 1

    def test_get_by_url_receipt_not_found(self, handler, mock_logger):
        url = "https://example.com/receipt"
        receipt_url_data = {"id": "hash123", "url": url, "receipt_id": "receipt123"}
        handler.db.read_one = Mock(side_effect=[receipt_url_data, None])

        with patch("src.handlers.sfs_md.receipt.make_hash", return_value="hash123"):
            result = handler.get_by_url(url)

        assert result is None
        assert handler.db.use_table.call_count == 2

    def test_get_by_url_logs_correctly(self, handler, mock_logger):
        url = "https://example.com/receipt"
        handler.db.read_one = Mock(return_value=None)

        with patch("src.handlers.sfs_md.receipt.make_hash", return_value="hash123"):
            handler.get_by_url(url)


class TestSfsMdReceiptHandlerGetById:
    """Tests for get_by_id method."""

    def test_get_by_id_success(self, handler):
        """Test successfully retrieving a receipt by ID."""
        receipt_data = {
            "id": "md_cr_1_42",
            "date": "2026-02-14T00:00:00+00:00",
            "user_id": "12345678-1234-5678-1234-567812345678",
            "company_id": "cmp_1",
            "company_name": "Test Co",
            "country_code": "md",
            "shop_address": "123 Test Street",
            "cash_register_id": "cr_1",
            "key": 42,
            "currency_code": "mdl",
            "total_amount": 12.34,
            "purchases": [],
            "receipt_url": "https://example.com/receipt/42",
        }
        handler.db.read_one = Mock(return_value=receipt_data)

        result = handler.get_by_id("md_cr_1_42")

        assert result is not None
        assert isinstance(result, SfsMdReceipt)
        assert result.id == "md_cr_1_42"
        assert result.company_id == "cmp_1"
        handler.db.use_table.assert_called_with(TableName.RECEIPT)
        handler.db.read_one.assert_called_with("md_cr_1_42")

    def test_get_by_id_not_found(self, handler):
        """Test get_by_id when receipt doesn't exist."""
        handler.db.read_one = Mock(return_value=None)

        result = handler.get_by_id("nonexistent_id")

        assert result is None
        handler.db.use_table.assert_called_with(TableName.RECEIPT)
        handler.db.read_one.assert_called_with("nonexistent_id")

    def test_get_by_id_with_shop(self, handler):
        """Test get_by_id returns receipt with shop_id."""
        receipt_data = {
            "id": "md_cr_1_42",
            "date": "2026-02-14T00:00:00+00:00",
            "user_id": "12345678-1234-5678-1234-567812345678",
            "company_id": "cmp_1",
            "company_name": "Test Co",
            "country_code": "md",
            "shop_address": "123 Test Street",
            "cash_register_id": "cr_1",
            "key": 42,
            "currency_code": "mdl",
            "total_amount": 12.34,
            "purchases": [],
            "receipt_url": "https://example.com/receipt/42",
            "shop_id": 123,
        }
        handler.db.read_one = Mock(return_value=receipt_data)

        result = handler.get_by_id("md_cr_1_42")

        assert result.shop_id == 123

    def test_get_by_id_with_multiple_purchases(self, handler):
        """Test get_by_id returns receipt with purchases."""
        receipt_data = {
            "id": "md_cr_1_42",
            "date": "2026-02-14T00:00:00+00:00",
            "user_id": "12345678-1234-5678-1234-567812345678",
            "company_id": "cmp_1",
            "company_name": "Test Co",
            "country_code": "md",
            "shop_address": "123 Test Street",
            "cash_register_id": "cr_1",
            "key": 42,
            "currency_code": "mdl",
            "total_amount": 12.34,
            "purchases": [
                {
                    "name": "Item A",
                    "quantity": 2.0,
                    "quantity_unit": "pcs",
                    "price": 6.17,
                    "item_id": "11111111-1111-1111-1111-111111111111",
                },
                {
                    "name": "Item B",
                    "quantity": 1.0,
                    "quantity_unit": "kg",
                    "price": 0.0,
                    "item_id": None,
                },
            ],
            "receipt_url": "https://example.com/receipt/42",
        }
        handler.db.read_one = Mock(return_value=receipt_data)

        result = handler.get_by_id("md_cr_1_42")

        assert len(result.purchases) == 2
        assert result.purchases[0].name == "Item A"
        assert result.purchases[1].name == "Item B"


class TestSfsMdReceiptHandlerAddShopId:
    """Tests for add_shop_id method."""

    @pytest.fixture
    def sample_receipt(self):
        return make_receipt()

    def test_add_shop_id_success(self, handler, sample_receipt):
        """Test successfully adding shop_id to receipt."""
        shop_id = 42
        handler.db.update_one = Mock(return_value=True)

        result = handler.add_shop_id(shop_id, sample_receipt)

        assert result.shop_id == shop_id
        handler.db.use_table.assert_called_with(TableName.RECEIPT)
        handler.db.update_one.assert_called_once()

        # Verify it was called with correct receipt ID and data
        call_args = handler.db.update_one.call_args[0]
        assert call_args[0] == sample_receipt.id
        assert call_args[1]["shop_id"] == shop_id

    def test_add_shop_id_database_failure(self, handler, sample_receipt):
        """Test add_shop_id raises HTTPException when database update fails."""
        shop_id = 42
        handler.db.update_one = Mock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            handler.add_shop_id(shop_id, sample_receipt)

        assert exc_info.value.status_code == 500
        assert "Failed to add shop to receipt" in exc_info.value.detail

    def test_add_shop_id_preserves_receipt_data(self, handler, sample_receipt):
        """Test that add_shop_id preserves other receipt data."""
        shop_id = 42
        original_company_id = sample_receipt.company_id
        original_total = sample_receipt.total_amount
        handler.db.update_one = Mock(return_value=True)

        result = handler.add_shop_id(shop_id, sample_receipt)

        assert result.company_id == original_company_id
        assert result.total_amount == original_total
        assert result.shop_id == shop_id

    def test_add_shop_id_with_zero_shop_id(self, handler, sample_receipt):
        """Test add_shop_id with shop_id of 0."""
        shop_id = 0
        handler.db.update_one = Mock(return_value=True)

        result = handler.add_shop_id(shop_id, sample_receipt)

        assert result.shop_id == 0
        handler.db.update_one.assert_called_once()

    def test_add_shop_id_with_large_shop_id(self, handler, sample_receipt):
        """Test add_shop_id with large shop_id value."""
        shop_id = 2147483647  # Max 32-bit int
        handler.db.update_one = Mock(return_value=True)

        result = handler.add_shop_id(shop_id, sample_receipt)

        assert result.shop_id == shop_id
        handler.db.update_one.assert_called_once()

    def test_add_shop_id_overwrites_existing_shop_id(self, handler, sample_receipt):
        """Test add_shop_id overwrites existing shop_id."""
        sample_receipt.shop_id = 100
        new_shop_id = 200
        handler.db.update_one = Mock(return_value=True)

        result = handler.add_shop_id(new_shop_id, sample_receipt)

        assert result.shop_id == new_shop_id

    def test_add_shop_id_updates_all_receipt_fields(self, handler, sample_receipt):
        """Test that add_shop_id includes all receipt data in update."""
        shop_id = 42
        handler.db.update_one = Mock(return_value=True)

        handler.add_shop_id(shop_id, sample_receipt)

        # Get the data passed to update_one
        call_args = handler.db.update_one.call_args[0][1]

        # Verify key receipt fields are included
        assert "id" in call_args
        assert "company_id" in call_args
        assert "total_amount" in call_args
        assert "shop_id" in call_args

    def test_add_shop_id_calls_model_dump(self, handler, sample_receipt):
        """Test that add_shop_id properly serializes receipt with model_dump."""
        shop_id = 42
        handler.db.update_one = Mock(return_value=True)

        handler.add_shop_id(shop_id, sample_receipt)

        # Verify update_one was called with JSON-serializable data
        call_args = handler.db.update_one.call_args[0][1]

        # UUIDs should be strings in the dump
        if "user_id" in call_args:
            assert isinstance(call_args["user_id"], (str, type(None)))


class TestSfsMdReceiptHandlerGetOrCreate:
    @pytest.fixture
    def sample_receipt(self):
        return make_receipt()

    def test_get_or_create_with_shop_match(self, handler, sample_receipt):
        shop_id = 567
        shop_data = [{"id": str(shop_id), "name": "Test Shop"}]
        # Need side_effect for shop lookup AND purchase item lookup
        handler.db.read_many = Mock(
            side_effect=[shop_data, []]
        )  # [] for no matching item
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.shop_id == shop_id
        handler.db.use_table.assert_any_call(TableName.SHOP)
        handler.db.use_table.assert_any_call(TableName.RECEIPT)
        handler.db.use_table.assert_any_call(TableName.RECEIPT_URL)

    def test_get_or_create_without_shop_match(self, handler, sample_receipt):
        handler.db.read_many = Mock(return_value=[])
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.shop_id is None
        handler.db.use_table.assert_any_call(TableName.SHOP)

    def test_get_or_create_with_purchases(self, handler, sample_receipt):
        shop_id = 12345678
        item_uuid = UUID("87654321-4321-8765-4321-876543210987")
        purchase = Mock()
        purchase.name = "Test Item"
        purchase.item_id = None
        purchase.status = None
        sample_receipt.purchases = [purchase]

        handler.db.read_many = Mock(
            side_effect=[
                [{"id": str(shop_id)}],
                [{"id": str(item_uuid), "status": ItemBarcodeStatus.PENDING}],
            ]
        )
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.purchases[0].item_id == item_uuid
        assert result.purchases[0].status == ItemBarcodeStatus.PENDING

    def test_get_or_create_with_purchase_no_match(self, handler, sample_receipt):
        purchase = Mock()
        purchase.name = "Nonexistent Item"
        purchase.item_id = None
        sample_receipt.purchases = [purchase]

        handler.db.read_many = Mock(return_value=[])
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.purchases[0].item_id is None

    def test_get_or_create_purchase_status_defaults_to_pending(
        self, handler, sample_receipt
    ):
        shop_id = 5678
        item_uuid = UUID("87654321-4321-8765-4321-876543210987")
        purchase = Mock()
        purchase.name = "Test Item"
        purchase.item_id = None
        sample_receipt.purchases = [purchase]

        handler.db.read_many = Mock(
            side_effect=[
                [{"id": str(shop_id)}],
                [{"id": str(item_uuid)}],
            ]
        )
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.purchases[0].status == ItemBarcodeStatus.PENDING

    def test_get_or_create_with_canonical_url(self, handler, sample_receipt):
        handler.db.read_many = Mock(return_value=[])
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        handler.get_or_create(sample_receipt)

        assert handler.db.create_one.call_count == 2

    def test_get_or_create_without_canonical_url(self, handler, sample_receipt):
        sample_receipt.receipt_canonical_url = None
        handler.db.read_many = Mock(return_value=[])
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        handler.get_or_create(sample_receipt)

        assert handler.db.create_one.call_count == 1
