from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from src.handlers.sfs_md.receipt import SfsMdReceiptHandler
from src.schemas.common import TableName, ItemBarcodeStatus
from src.schemas.sfs_md.receipt import SfsMdReceipt
from src.tests.unit import make_receipt


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_db():
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

        mock_logger.info.assert_called_with("receipt url: " + url)


class TestSfsMdReceiptHandlerGetOrCreate:
    @pytest.fixture
    def sample_receipt(self):
        return make_receipt()

    def test_get_or_create_with_shop_match(self, handler, sample_receipt):
        shop_uuid = UUID("12345678-1234-5678-1234-567812345678")
        shop_data = [{"id": str(shop_uuid), "name": "Test Shop"}]
        # Need side_effect for shop lookup AND purchase item lookup
        handler.db.read_many = Mock(side_effect=[shop_data, []])  # [] for no matching item
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.shop_id == shop_uuid
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
        shop_uuid = UUID("12345678-1234-5678-1234-567812345678")
        item_uuid = UUID("87654321-4321-8765-4321-876543210987")
        purchase = Mock(name="Test Item", item_id=None, status=None)
        sample_receipt.purchases = [purchase]
        
        handler.db.read_many = Mock(
            side_effect=[
                [{"id": str(shop_uuid)}],
                [{"id": str(item_uuid), "status": ItemBarcodeStatus.PENDING}],
            ]
        )
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.purchases[0].item_id == item_uuid
        assert result.purchases[0].status == ItemBarcodeStatus.PENDING

    def test_get_or_create_with_purchase_no_match(self, handler, sample_receipt):
        purchase = Mock(name="Nonexistent Item", item_id=None)
        sample_receipt.purchases = [purchase]
        
        handler.db.read_many = Mock(side_effect=[[], []])
        handler.db.create_or_update_one = Mock()
        handler.db.create_one = Mock()

        result = handler.get_or_create(sample_receipt)

        assert result.purchases[0].item_id is None

    def test_get_or_create_purchase_status_defaults_to_pending(self, handler, sample_receipt):
        shop_uuid = UUID("12345678-1234-5678-1234-567812345678")
        item_uuid = UUID("87654321-4321-8765-4321-876543210987")
        purchase = Mock(name="Test Item", item_id=None)
        sample_receipt.purchases = [purchase]
        
        handler.db.read_many = Mock(
            side_effect=[
                [{"id": str(shop_uuid)}],
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