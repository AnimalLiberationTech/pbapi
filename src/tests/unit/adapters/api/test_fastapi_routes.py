import asyncio
import logging
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from starlette.requests import Request

from src.adapters.api import fastapi_routes
from src.schemas.common import QuantityUnit
from src.schemas.purchased_item import PurchasedItem
from src.schemas.request_schemas import GetOrCreateUserByIdentityRequest
from src.schemas.response_schemas import ApiResponse
from src.schemas.shop import Shop
from src.schemas.user_identity import IdentityProvider
from src.tests.unit import make_receipt


def run_async(coro):
    return asyncio.run(coro)


def make_request(scope_overrides=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    if scope_overrides:
        scope.update(scope_overrides)
    return Request(scope)


class TestGetLogger:
    def test_returns_appwrite_logger_when_context_present(self):
        mock_logger = Mock(spec=logging.Logger)
        request = make_request({"appwrite_context": Mock()})

        with patch("src.adapters.api.fastapi_routes.AppwriteLogger") as mock_appwrite:
            mock_appwrite.return_value.log = mock_logger
            result = fastapi_routes.get_logger(request)

        assert result is mock_logger
        mock_appwrite.assert_called_once()

    def test_returns_default_logger_when_no_context(self):
        mock_logger = Mock(spec=logging.Logger)
        request = make_request()

        with patch("src.adapters.api.fastapi_routes.DefaultLogger") as mock_default:
            mock_default.return_value.log = mock_logger
            result = fastapi_routes.get_logger(request)

        assert result is mock_logger
        mock_default.assert_called_once_with(level=logging.DEBUG)


class TestUserRoutes:
    def test_get_or_create_user_by_identity_calls_handler(self):
        logger = Mock()
        request = GetOrCreateUserByIdentityRequest(
            id="google_123",
            provider=IdentityProvider.GOOGLE,
            email="test@example.com",
            name="Test User",
        )
        expected_user = {"id": "user_1"}

        with patch(
            "src.adapters.api.fastapi_routes.UserIdentityHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create_user_by_identity.return_value = (
                expected_user
            )

            result = run_async(
                fastapi_routes.get_or_create_user_by_identity(request, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "User retrieved or created successfully"
        assert result.data == expected_user
        logger.info.assert_called_with("User identity: google_123 for provider: google")
        mock_handler.assert_called_once_with(logger)
        mock_handler.return_value.get_or_create_user_by_identity.assert_called_once_with(
            "google_123",
            IdentityProvider.GOOGLE,
            "test@example.com",
            "Test User",
        )

    def test_get_or_create_user_by_identity_allows_none_email(self):
        logger = Mock()
        request = GetOrCreateUserByIdentityRequest(
            id="g_456",
            provider=IdentityProvider.GOOGLE,
            email=None,
            name="Google User",
        )

        with patch(
            "src.adapters.api.fastapi_routes.UserIdentityHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create_user_by_identity.return_value = {
                "id": "user_2"
            }

            run_async(
                fastapi_routes.get_or_create_user_by_identity(request, logger=logger)
            )

        mock_handler.return_value.get_or_create_user_by_identity.assert_called_once_with(
            "g_456",
            IdentityProvider.GOOGLE,
            None,
            "Google User",
        )


class TestReceiptRoutes:
    def test_get_or_create_receipt_calls_handler(self):
        logger = Mock()
        request = make_receipt()
        expected_receipt = {"id": "receipt_1"}

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = expected_receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(request, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Receipt retrieved or created successfully"
        assert result.data == expected_receipt
        logger.info.assert_called_with("Receipt URL: https://example.com/receipt/42")
        mock_handler.assert_called_once_with(logger)
        mock_handler.return_value.get_or_create.assert_called_once_with(request)

    def test_get_or_create_receipt_with_multiple_purchases(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.purchases = [
            PurchasedItem(
                name="Item A", quantity=2.0, unit=QuantityUnit.PIECE, price=6.17
            ),
            PurchasedItem(
                name="Item B", quantity=1.5, unit=QuantityUnit.KILOGRAM, price=10.50
            ),
            PurchasedItem(
                name="Item C", quantity=3.0, unit=QuantityUnit.PIECE, price=5.00
            ),
        ]

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert len(result.data.purchases) == 3
        mock_handler.return_value.get_or_create.assert_called_once_with(receipt)

    def test_get_receipt_by_url_found(self):
        logger = Mock()
        receipt = make_receipt()
        url = "https://example.com/receipt/42"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_url.return_value = receipt

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)
            result = run_async(
                fastapi_routes.get_receipt_by_url(request, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Receipt retrieved successfully"
        assert result.data == receipt
        logger.info.assert_called_with(f"Receipt URL: {url}")
        mock_handler.return_value.get_by_url.assert_called_once_with(url)

    def test_get_receipt_by_url_not_found(self):
        logger = Mock()
        url = "https://example.com/nonexistent/receipt"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_url.return_value = None

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)

            with pytest.raises(HTTPException) as exc_info:
                run_async(fastapi_routes.get_receipt_by_url(request, logger=logger))

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Receipt not found"
        mock_handler.return_value.get_by_url.assert_called_once_with(url)

    def test_get_receipt_by_url_with_special_characters(self):
        logger = Mock()
        url = "https://example.com/receipt/42?param=value&other=test#anchor"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            receipt = make_receipt()
            receipt.receipt_url = url
            mock_handler.return_value.get_by_url.return_value = receipt

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)
            result = run_async(
                fastapi_routes.get_receipt_by_url(request, logger=logger)
            )

        assert result.data.receipt_url == url
        mock_handler.return_value.get_by_url.assert_called_once_with(url)

    def test_get_or_create_receipt_handler_initialization(self):
        logger = Mock()
        request = make_receipt()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = request

            run_async(fastapi_routes.get_or_create_receipt(request, logger=logger))

        # Verify handler was initialized with the logger
        mock_handler.assert_called_once_with(logger)

    def test_get_receipt_by_url_empty_url_string(self):
        logger = Mock()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_url.return_value = None

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url="")

            with pytest.raises(HTTPException) as exc_info:
                run_async(fastapi_routes.get_receipt_by_url(request, logger=logger))

            assert exc_info.value.status_code == 404
        mock_handler.return_value.get_by_url.assert_called_once_with("")

    def test_get_or_create_receipt_preserves_all_fields(self):
        logger = Mock()
        request = make_receipt()
        request.shop_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = request

            result = run_async(
                fastapi_routes.get_or_create_receipt(request, logger=logger)
            )

        assert result.data.shop_id == request.shop_id
        assert result.data.date == request.date
        assert result.data.user_id == request.user_id
        assert result.data.total_amount == request.total_amount

    # Edge case tests
    def test_get_receipt_by_url_long_url(self):
        logger = Mock()
        long_url = "https://example.com/" + "a" * 1000 + "/receipt/42"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            receipt = make_receipt()
            receipt.receipt_url = long_url
            mock_handler.return_value.get_by_url.return_value = receipt

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=long_url)
            result = run_async(
                fastapi_routes.get_receipt_by_url(request, logger=logger)
            )

        assert result.data.receipt_url == long_url
        mock_handler.return_value.get_by_url.assert_called_once_with(long_url)

    def test_get_receipt_by_url_unicode_characters(self):
        logger = Mock()
        url_with_unicode = "https://example.com/receipt/42?name=тест&item=café"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            receipt = make_receipt()
            receipt.receipt_url = url_with_unicode
            mock_handler.return_value.get_by_url.return_value = receipt

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url_with_unicode)
            result = run_async(
                fastapi_routes.get_receipt_by_url(request, logger=logger)
            )

        assert result.data.receipt_url == url_with_unicode

    def test_get_or_create_receipt_zero_total_amount(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.total_amount = 0.0

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert result.data.total_amount == 0.0

    def test_get_or_create_receipt_negative_total_amount(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.total_amount = -10.50

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert result.data.total_amount == -10.50

    def test_get_or_create_receipt_very_large_amount(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.total_amount = 999999.99

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert result.data.total_amount == 999999.99

    def test_get_or_create_receipt_with_single_purchase(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.purchases = [
            PurchasedItem(
                name="Single Item", quantity=1.0, unit=QuantityUnit.PIECE, price=5.00
            ),
        ]

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert len(result.data.purchases) == 1
        assert result.data.purchases[0].name == "Single Item"

    def test_get_or_create_receipt_with_many_purchases(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.purchases = [
            PurchasedItem(
                name=f"Item {i}",
                quantity=float(i),
                unit=QuantityUnit.PIECE,
                price=float(i),
            )
            for i in range(1, 101)  # 100 items
        ]

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert len(result.data.purchases) == 100

    def test_get_receipt_by_url_handler_exception(self):
        logger = Mock()
        url = "https://example.com/receipt/42"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_url.side_effect = Exception(
                "Database connection error"
            )

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)

            try:
                run_async(fastapi_routes.get_receipt_by_url(request, logger=logger))
                assert False, "Expected exception to be raised"
            except Exception as e:
                assert str(e) == "Database connection error"

    def test_get_or_create_receipt_handler_exception(self):
        logger = Mock()
        receipt = make_receipt()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.side_effect = ValueError(
                "Invalid receipt data"
            )

            try:
                run_async(fastapi_routes.get_or_create_receipt(receipt, logger=logger))
                assert False, "Expected exception to be raised"
            except ValueError as e:
                assert str(e) == "Invalid receipt data"

    def test_get_receipt_by_url_same_handler_instance(self):
        """Verify handler instance is consistent across calls"""
        logger = Mock()
        url = "https://example.com/receipt/42"
        receipt = make_receipt()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.get_by_url.return_value = receipt

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)
            result = run_async(
                fastapi_routes.get_receipt_by_url(request, logger=logger)
            )

            # Verify the handler was instantiated with logger
            mock_handler.assert_called_once_with(logger)
            assert isinstance(result, ApiResponse)
            assert result.data == receipt

    def test_get_or_create_receipt_with_optional_shop_id_none(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.shop_id = None

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert result.data.shop_id is None

    def test_get_or_create_receipt_with_optional_canonical_url_none(self):
        logger = Mock()
        receipt = make_receipt()
        receipt.receipt_canonical_url = None

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            result = run_async(
                fastapi_routes.get_or_create_receipt(receipt, logger=logger)
            )

        assert result.data.receipt_canonical_url is None

    def test_get_receipt_by_url_logging_called(self):
        logger = Mock()
        url = "https://example.com/receipt/42"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_url.return_value = None

            from src.schemas.request_schemas import GetReceiptByUrlRequest

            request = GetReceiptByUrlRequest(url=url)

            with pytest.raises(HTTPException):
                run_async(fastapi_routes.get_receipt_by_url(request, logger=logger))

        # Verify logging was called with correct message before exception
        logger.info.assert_called_once_with(f"Receipt URL: {url}")

    def test_get_or_create_receipt_logging_called(self):
        logger = Mock()
        receipt = make_receipt()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_or_create.return_value = receipt

            run_async(fastapi_routes.get_or_create_receipt(receipt, logger=logger))

        # Verify logging was called with receipt URL
        logger.info.assert_called_once_with(
            "Receipt URL: https://example.com/receipt/42"
        )


class TestHealthRoutes:
    def test_health_returns_default_message(self):
        logger = Mock()

        result = run_async(fastapi_routes.health(logger=logger))

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Plant-Based API health check successful"
        logger.info.assert_called_with("Plant-Based API health endpoint called")

    def test_home_calls_health(self):
        logger = Mock()

        result = run_async(fastapi_routes.home(logger=logger))

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert logger.info.call_count == 2
        logger.info.assert_any_call("Plant-Based API home endpoint called")
        logger.info.assert_any_call("Plant-Based API health endpoint called")

    def test_deep_ping_sleeps_and_returns_health(self):
        logger = Mock()

        with patch("src.adapters.api.fastapi_routes.time.sleep") as mock_sleep:
            result = run_async(fastapi_routes.deep_ping(logger=logger))

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Plant-Based API deep ping successful"
        mock_sleep.assert_called_once_with(1)
        logger.info.assert_called_with("Plant-Based API deep ping endpoint called")


class TestReceiptRoutesGetById:
    """Tests for GET /receipt/get-by-id endpoint."""

    def test_get_receipt_by_id_success(self):
        """Test successfully retrieving receipt by ID."""
        logger = Mock()
        receipt_id = "md_cr_1_42"
        receipt = make_receipt()
        receipt.id = receipt_id

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = receipt

            result = run_async(
                fastapi_routes.get_receipt_by_id(receipt_id, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Receipt retrieved successfully"
        assert result.data.id == receipt_id
        logger.info.assert_called_once_with(f"Receipt ID: {receipt_id}")
        mock_handler.return_value.get_by_id.assert_called_once_with(receipt_id)

    def test_get_receipt_by_id_not_found(self):
        """Test 404 when receipt doesn't exist."""
        logger = Mock()
        receipt_id = "nonexistent_id"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(fastapi_routes.get_receipt_by_id(receipt_id, logger=logger))

            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Receipt not found"
        mock_handler.return_value.get_by_id.assert_called_once_with(receipt_id)

    def test_get_receipt_by_id_with_shop(self):
        """Test retrieving receipt with associated shop."""
        logger = Mock()
        receipt_id = "md_cr_1_42"
        receipt = make_receipt()
        receipt.id = receipt_id
        receipt.shop_id = 42

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = receipt

            result = run_async(
                fastapi_routes.get_receipt_by_id(receipt_id, logger=logger)
            )

        assert result.data.shop_id == 42

    def test_get_receipt_by_id_logging(self):
        """Test that logging happens before retrieving receipt."""
        logger = Mock()
        receipt_id = "md_cr_1_42"

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = None

            with pytest.raises(HTTPException):
                run_async(fastapi_routes.get_receipt_by_id(receipt_id, logger=logger))

        logger.info.assert_called_once_with(f"Receipt ID: {receipt_id}")

    def test_get_receipt_by_id_handler_initialization(self):
        """Test that handler is initialized with logger."""
        logger = Mock()
        receipt_id = "md_cr_1_42"
        receipt = make_receipt()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = receipt

            run_async(fastapi_routes.get_receipt_by_id(receipt_id, logger=logger))

        mock_handler.assert_called_once_with(logger)

    def test_get_receipt_by_id_with_empty_string(self):
        """Test get_receipt_by_id with empty receipt ID."""
        logger = Mock()

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(fastapi_routes.get_receipt_by_id("", logger=logger))

            assert exc_info.value.status_code == 404
        mock_handler.return_value.get_by_id.assert_called_once_with("")

    def test_get_receipt_by_id_preserves_all_fields(self):
        """Test that all receipt fields are preserved."""
        logger = Mock()
        receipt_id = "md_cr_1_42"
        receipt = make_receipt()
        receipt.id = receipt_id
        receipt.shop_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = receipt

            result = run_async(
                fastapi_routes.get_receipt_by_id(receipt_id, logger=logger)
            )

        assert result.data.id == receipt_id
        assert result.data.user_id == receipt.user_id
        assert result.data.total_amount == receipt.total_amount
        assert result.data.date == receipt.date

    def test_get_receipt_by_id_with_special_characters(self):
        """Test receipt ID with special characters."""
        logger = Mock()
        receipt_id = "md_cr_1_42_special-chars_123"
        receipt = make_receipt()
        receipt.id = receipt_id

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_handler.return_value.get_by_id.return_value = receipt

            result = run_async(
                fastapi_routes.get_receipt_by_id(receipt_id, logger=logger)
            )

        assert result.data.id == receipt_id


class TestAddShopRoute:
    """Tests for POST /receipt/add-shop-id endpoint."""

    def test_add_shop_success(self):
        """Test successfully adding shop to receipt."""
        logger = Mock()
        receipt = make_receipt()
        shop_id = 42
        request = Mock()
        request.shop_id = shop_id
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.return_value = receipt
            receipt.shop_id = shop_id

            result = run_async(
                fastapi_routes.add_shop(request, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Shop linked to receipt successfully"
        assert result.data.shop_id == shop_id
        mock_handler.assert_called_once_with(logger)
        mock_instance.add_shop_id.assert_called_once_with(
            shop_id=shop_id, receipt=receipt
        )

    def test_add_shop_handler_initialization(self):
        """Test handler is initialized with logger."""
        logger = Mock()
        receipt = make_receipt()
        request = Mock()
        request.shop_id = 42
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.return_value = receipt

            run_async(fastapi_routes.add_shop(request, logger=logger))

        mock_handler.assert_called_once_with(logger)

    def test_add_shop_with_zero_shop_id(self):
        """Test adding shop with ID 0."""
        logger = Mock()
        receipt = make_receipt()
        request = Mock()
        request.shop_id = 0
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.return_value = receipt
            receipt.shop_id = 0

            result = run_async(
                fastapi_routes.add_shop(request, logger=logger)
            )

        assert result.data.shop_id == 0

    def test_add_shop_with_large_shop_id(self):
        """Test adding shop with large ID."""
        logger = Mock()
        receipt = make_receipt()
        large_id = 2147483647
        request = Mock()
        request.shop_id = large_id
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.return_value = receipt
            receipt.shop_id = large_id

            result = run_async(
                fastapi_routes.add_shop(request, logger=logger)
            )

        assert result.data.shop_id == large_id

    def test_add_shop_preserves_receipt_data(self):
        """Test that receipt data is preserved."""
        logger = Mock()
        receipt = make_receipt()
        original_total = receipt.total_amount
        original_company = receipt.company_id
        request = Mock()
        request.shop_id = 42
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.return_value = receipt

            result = run_async(
                fastapi_routes.add_shop(request, logger=logger)
            )

        assert result.data.total_amount == original_total
        assert result.data.company_id == original_company

    def test_add_shop_overwrites_existing_shop_id(self):
        """Test overwriting existing shop_id."""
        logger = Mock()
        receipt = make_receipt()
        receipt.shop_id = 100
        new_shop_id = 200
        request = Mock()
        request.shop_id = new_shop_id
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            updated_receipt = make_receipt()
            updated_receipt.shop_id = new_shop_id
            mock_instance.add_shop_id.return_value = updated_receipt

            result = run_async(
                fastapi_routes.add_shop(request, logger=logger)
            )

        mock_instance.add_shop_id.assert_called_once_with(
            shop_id=new_shop_id, receipt=receipt
        )

    def test_add_shop_handler_exception(self):
        """Test handling of handler exceptions."""
        logger = Mock()
        receipt = make_receipt()
        request = Mock()
        request.shop_id = 42
        request.receipt = receipt

        with patch(
            "src.adapters.api.fastapi_routes.SfsMdReceiptHandler"
        ) as mock_handler:
            mock_instance = Mock()
            mock_handler.return_value = mock_instance
            mock_instance.add_shop_id.side_effect = HTTPException(
                status_code=500, detail="Failed to add shop"
            )

            with pytest.raises(HTTPException) as exc_info:
                run_async(fastapi_routes.add_shop(request, logger=logger))

            assert exc_info.value.status_code == 500
            assert "Failed to add shop" in exc_info.value.detail


class TestShopRoutes:
    """Tests for /shop endpoints."""

    def test_get_or_create_shop_success(self):
        """Test successfully getting or creating a shop."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.return_value = shop

            result = run_async(
                fastapi_routes.get_or_create_shop(shop, logger=logger)
            )

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Shop retrieved or created successfully"
        assert result.data == shop
        logger.info.assert_called_once()
        mock_handler.assert_called_once_with(logger)
        mock_handler.return_value.get_or_create.assert_called_once_with(shop)

    def test_get_or_create_shop_handler_initialization(self):
        """Test handler is initialized with logger."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.return_value = shop

            run_async(fastapi_routes.get_or_create_shop(shop, logger=logger))

        mock_handler.assert_called_once_with(logger)

    def test_get_or_create_shop_with_existing_id(self):
        """Test get_or_create with shop that has an ID."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            id=42,
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.return_value = shop

            result = run_async(
                fastapi_routes.get_or_create_shop(shop, logger=logger)
            )

        assert result.data.id == 42

    def test_get_or_create_shop_preserves_all_fields(self):
        """Test that all shop fields are preserved."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            id=42,
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.return_value = shop

            result = run_async(
                fastapi_routes.get_or_create_shop(shop, logger=logger)
            )

        assert result.data.id == shop.id
        assert result.data.company_id == shop.company_id
        assert result.data.address == shop.address
        assert result.data.country_code == shop.country_code

    def test_get_or_create_shop_logging(self):
        """Test that shop request is logged."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.return_value = shop

            run_async(fastapi_routes.get_or_create_shop(shop, logger=logger))

        logger.info.assert_called_once()
        assert "Get or create shop request:" in logger.info.call_args[0][0]

    def test_get_or_create_shop_handler_exception(self):
        """Test handling of handler exceptions."""
        logger = Mock()
        from src.schemas.osm_data import OsmData
        from src.schemas.common import OsmType, CountryCode

        osm_data = OsmData(
            type=OsmType.NODE,
            key=123456,
            lat="47.0293446",
            lon="28.8638389",
            display_name="Test Shop",
        )
        shop = Shop(
            country_code=CountryCode.MOLDOVA,
            company_id="5897403875",
            address="Test Address",
            osm_data=osm_data,
            creator_user_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        with patch("src.adapters.api.fastapi_routes.ShopHandler") as mock_handler:
            mock_handler.return_value.get_or_create.side_effect = ValueError(
                "Invalid shop data"
            )

            with pytest.raises(ValueError) as exc_info:
                run_async(fastapi_routes.get_or_create_shop(shop, logger=logger))

            assert "Invalid shop data" in str(exc_info.value)

