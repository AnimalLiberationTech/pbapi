from unittest import TestCase

import os
import sys
import warnings
from unittest.mock import MagicMock, patch

# Suppress testcontainers deprecation warning about @wait_container_is_ready
warnings.filterwarnings(
    "ignore", message=".*wait_container_is_ready.*", category=DeprecationWarning
)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from testcontainers.postgres import PostgresContainer

from src.adapters.db.postgresql_core import PostgreSQLCoreAdapter
from src.handlers.parse_from_url import parse_from_url_handler
from src.schemas.common import EnvType, TableName
from src.tests import load_stub_file, USER_ID_1
from src.tests.stubs.receipts.sfs_md.expected_objects import KL_RECEIPT

KL_RECEIPT_PATH = os.path.join("receipts", "sfs_md", "kaufland.html")


class TestParseFromUrlHandlerPostgres(TestCase):
    container = None
    adapter = None

    @classmethod
    def setUpClass(cls):
        cls.container = PostgresContainer("postgres:15.14-alpine")
        cls.container.start()

        os.environ["TEST_POSTGRES_HOST"] = cls.container.get_container_host_ip()
        os.environ["TEST_POSTGRES_PORT"] = str(cls.container.get_exposed_port(5432))
        os.environ["TEST_POSTGRES_DB"] = cls.container.dbname
        os.environ["TEST_POSTGRES_USER"] = cls.container.username
        os.environ["TEST_POSTGRES_PASSWORD"] = cls.container.password
        os.environ["ENV_NAME"] = "test"
        os.environ["TEST_COSMOS_DB_DATABASE_ID"] = (
            "test_db"  # Mock for init_db_session logic
        )

    @classmethod
    def tearDownClass(cls):
        cls.container.stop()

    def setUp(self):
        self.logger = MagicMock()
        self.adapter = PostgreSQLCoreAdapter(EnvType.TEST, self.logger)

        # Create tables
        self.adapter.create_table(TableName.RECEIPT)
        self.adapter.create_table(TableName.RECEIPT_URL)
        self.adapter.create_table(TableName.SHOP)
        self.adapter.create_table(TableName.SHOP_ITEM)

    def tearDown(self):
        # Clean up tables
        self.adapter.drop_table(TableName.RECEIPT)
        self.adapter.drop_table(TableName.RECEIPT_URL)
        self.adapter.drop_table(TableName.SHOP)
        self.adapter.drop_table(TableName.SHOP_ITEM)

    @patch("src.parsers.sfs_md.receipt_parser.init_db_session")
    @patch("src.handlers.parse_from_url.get_html")
    def test_parse_from_url_handler_success(self, mock_get_html, mock_init_db_session):
        # Setup mocks
        mock_init_db_session.return_value = self.adapter
        mock_get_html.return_value = load_stub_file(KL_RECEIPT_PATH)

        url = KL_RECEIPT.receipt_url
        user_id = USER_ID_1

        status, response = parse_from_url_handler(url, user_id, self.logger)

        if status != 200:
            print(f"Status: {status}")
            print(f"Response: {response}")
            print("Logger calls:")
            for call in self.logger.mock_calls:
                print(call)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Receipt successfully processed")
        self.assertEqual(response["data"]["_id"], KL_RECEIPT.id)

        self.adapter.use_table(TableName.RECEIPT)
        receipt_in_db = self.adapter.read_one(KL_RECEIPT.id)
        self.assertIsNotNone(receipt_in_db)
        self.assertEqual(receipt_in_db["total_amount"], KL_RECEIPT.total_amount)

        self.adapter.use_table(TableName.RECEIPT_URL)
        receipt_urls = self.adapter.read_many()
        self.assertTrue(len(receipt_urls) >= 1)
        found = False
        for r_url in receipt_urls:
            if r_url["url"] == url:
                found = True
                break
        self.assertTrue(found)

    @patch("src.parsers.sfs_md.receipt_parser.init_db_session")
    @patch("src.handlers.parse_from_url.get_html")
    def test_parse_from_url_handler_already_exists(
        self, mock_get_html, mock_init_db_session
    ):
        # Setup mocks
        mock_init_db_session.return_value = self.adapter

        # Pre-populate DB
        self.adapter.use_table(TableName.RECEIPT)
        self.adapter.create_one(KL_RECEIPT.model_dump(mode="json"))

        from src.helpers.common import make_hash
        from src.schemas.receipt_url import ReceiptUrl

        url = KL_RECEIPT.receipt_url
        receipt_url = ReceiptUrl(id=make_hash(url), url=url, receipt_id=KL_RECEIPT.id)
        self.adapter.use_table(TableName.RECEIPT_URL)
        self.adapter.create_one(receipt_url.model_dump(mode="json"))

        status, response = parse_from_url_handler(url, USER_ID_1, self.logger)

        if status != 200:
            print(f"Status: {status}")
            print(f"Response: {response}")
            print("Logger calls:")
            for call in self.logger.mock_calls:
                print(call)

        self.assertEqual(status, 200)
        self.assertEqual(response["msg"], "Receipt successfully processed")
        mock_get_html.assert_not_called()
        self.logger.info.assert_any_call("Receipt found in the db")
