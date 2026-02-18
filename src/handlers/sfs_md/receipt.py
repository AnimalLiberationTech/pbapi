from uuid import UUID

from src.adapters.db.postgresql import PostgreSQLAdapter, init_db_session
from src.helpers.common import make_hash
from src.schemas.common import TableName, ItemBarcodeStatus
from src.schemas.receipt_url import ReceiptUrl
from src.schemas.sfs_md.receipt import SfsMdReceipt


class SfsMdReceiptHandler:
    def __init__(self, logger):
        self.logger = logger
        self.db: PostgreSQLAdapter = init_db_session(self.logger)

    def get_by_id(self, receipt_id: str) -> SfsMdReceipt | None:
        self.db.use_table(TableName.RECEIPT)
        receipt = self.db.read_one(receipt_id)
        if receipt:
            return SfsMdReceipt(**receipt)
        return None

    def get_by_url(self, url: str) -> SfsMdReceipt | None:
        self.db.use_table(TableName.RECEIPT_URL)
        receipt_url = self.db.read_one(make_hash(url))

        if receipt_url:
            url = ReceiptUrl(**receipt_url)
            self.logger.info("receipt _id: " + url.receipt_id)

            self.db.use_table(TableName.RECEIPT)
            receipt = self.db.read_one(url.receipt_id)
            if receipt:
                return SfsMdReceipt(**receipt)
        return None

    def get_or_create(self, receipt: SfsMdReceipt) -> SfsMdReceipt:
        self.db.use_table(TableName.SHOP)
        shops = self.db.read_many(
            {
                "address": receipt.shop_address,
                "company_id": receipt.company_id,
                "country_code": receipt.country_code,
            },
            limit=1,
        )
        if shops:
            receipt.shop_id = int(shops[0]["id"])

            for i, purchase in enumerate(receipt.purchases):
                self.db.use_table(TableName.SHOP_ITEM)
                items = self.db.read_many(
                    {"name": purchase.name, "shop_id": receipt.shop_id},
                    limit=1,
                )
                if items:
                    receipt.purchases[i].item_id = UUID(items[0]["id"])
                    receipt.purchases[i].status = items[0].get(
                        "status", ItemBarcodeStatus.PENDING
                    )

        self.db.use_table(TableName.RECEIPT)
        self.db.create_or_update_one(receipt.model_dump(mode="json"))

        self.db.use_table(TableName.RECEIPT_URL)
        receipt_url = ReceiptUrl(url=receipt.receipt_url, receipt_id=receipt.id)
        self.db.create_one(receipt_url.model_dump(mode="json"))

        if receipt.receipt_canonical_url:
            receipt_url_canonical = ReceiptUrl(
                url=receipt.receipt_canonical_url,
                receipt_id=receipt.id,
            )
            self.db.create_one(receipt_url_canonical.model_dump(mode="json"))

        self.logger.info(receipt.model_dump())
        return receipt

    def add_shop_id(self, shop_id: int, receipt: SfsMdReceipt) -> SfsMdReceipt:
        self.db.use_table(TableName.RECEIPT)
        receipt.shop_id = shop_id
        self.db.update_one(receipt.id, receipt.model_dump(mode="json"))
        return receipt
