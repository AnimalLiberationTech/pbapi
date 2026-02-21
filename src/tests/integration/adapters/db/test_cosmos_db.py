from unittest import TestCase
from unittest.mock import Mock

from src.adapters.db.cosmos_db_core import CosmosDBCoreAdapter
from src.schemas.common import EnvType, TableName, TablePartitionKey
from src.tests import USER_ID_1
from src.tests.stubs.receipts.sfs_md.expected_objects import LIN_RECEIPT, KL_RECEIPT


class TestCosmosDBAdapter(TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        logger = Mock()
        cls.session = CosmosDBCoreAdapter(EnvType.TEST, logger)

    def setUp(self):
        self.session.create_table(
            TableName.RECEIPT, partition_key=TablePartitionKey.RECEIPT
        )

    def test_create_one(self):
        created_receipt_id = self.session.create_one(LIN_RECEIPT.model_dump(mode="json"))
        assert created_receipt_id == LIN_RECEIPT.id

    def test_read_one(self):
        created_receipt_id = self.session.create_one(LIN_RECEIPT.model_dump(mode="json"))
        receipt: dict = self.session.read_one(created_receipt_id, partition_key=USER_ID_1)
        assert receipt["_id"] == LIN_RECEIPT.id
        assert receipt["date"] == LIN_RECEIPT.date.isoformat()
        assert receipt["user_id"] == USER_ID_1
        assert receipt["company_id"] == LIN_RECEIPT.company_id
        assert receipt["company_name"] == LIN_RECEIPT.company_name
        assert receipt["country_code"] == LIN_RECEIPT.country_code
        assert receipt["shop_address"] == LIN_RECEIPT.shop_address
        assert receipt["cash_register_id"] == LIN_RECEIPT.cash_register_id
        assert receipt["total_amount"] == LIN_RECEIPT.total_amount
        assert receipt["currency_code"] == LIN_RECEIPT.currency_code
        assert receipt["receipt_url"] == LIN_RECEIPT.receipt_url
        assert len(receipt["purchases"]) == len(LIN_RECEIPT.purchases)

    def test_read_all(self):
        created_receipt_id_1 = self.session.create_one(
            LIN_RECEIPT.model_dump(mode="json")
        )
        created_receipt_id_2 = self.session.create_one(KL_RECEIPT.model_dump(mode="json"))
        receipts = self.session.read_many(partition_key=USER_ID_1)
        assert len(receipts) == 2
        assert receipts[0]["id"] == created_receipt_id_1 == LIN_RECEIPT.id
        assert receipts[1]["id"] == created_receipt_id_2 == KL_RECEIPT.id

    def test_read_many_where(self):
        self.session.create_one(LIN_RECEIPT.model_dump(mode="json"))
        created_receipt_id_2 = self.session.create_one(KL_RECEIPT.model_dump(mode="json"))
        receipts = self.session.read_many(
            {"company_id": KL_RECEIPT.company_id}, partition_key=USER_ID_1
        )
        assert len(receipts) == 1
        assert receipts[0]["_id"] == created_receipt_id_2 == KL_RECEIPT.id

    def test_update_one(self):
        total_amount = LIN_RECEIPT.total_amount
        receipt = LIN_RECEIPT.model_dump(mode="json")
        self.session.create_one(receipt)
        receipt["total_amount"] = total_amount + 100
        self.session.update_one(LIN_RECEIPT.id, receipt)
        receipt = self.session.read_one(LIN_RECEIPT.id, partition_key=USER_ID_1)
        assert receipt["total_amount"] == total_amount + 100

    def test_delete_one(self):
        created_receipt_id_1 = self.session.create_one(
            LIN_RECEIPT.model_dump(mode="json")
        )
        created_receipt_id_2 = self.session.create_one(KL_RECEIPT.model_dump(mode="json"))
        receipts = self.session.read_many(partition_key=USER_ID_1)
        assert len(receipts) == 2
        self.session.delete_one(created_receipt_id_1, partition_key=USER_ID_1)
        receipts = self.session.read_many(partition_key=USER_ID_1)
        assert len(receipts) == 1
        assert receipts[0]["_id"] == created_receipt_id_2 == KL_RECEIPT.id

    def tearDown(self):
        self.session.drop_table(TableName.RECEIPT)
