import asyncio
import logging
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from starlette.requests import Request

from src.adapters.api import fastapi_routes
from src.schemas.common import QuantityUnit
from src.schemas.request_schemas import GetOrCreateUserByIdentityRequest
from src.schemas.response_schemas import ApiResponse
from src.schemas.user_identity import IdentityProvider
from src.schemas.purchased_item import PurchasedItem
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
        logger.info.assert_called_with("Health endpoint called")

    def test_home_calls_health(self):
        logger = Mock()

        result = run_async(fastapi_routes.home(logger=logger))

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert logger.info.call_count == 2
        logger.info.assert_any_call("Plant-Based API home endpoint called")
        logger.info.assert_any_call("Health endpoint called")

    def test_deep_ping_sleeps_and_returns_health(self):
        logger = Mock()

        with patch("src.adapters.api.fastapi_routes.time.sleep") as mock_sleep:
            result = run_async(fastapi_routes.deep_ping(logger=logger))

        assert isinstance(result, ApiResponse)
        assert result.status_code == status.HTTP_200_OK
        assert result.detail == "Deep ping successful"
        mock_sleep.assert_called_once_with(1)
        logger.info.assert_called_with("Deep ping endpoint called")
