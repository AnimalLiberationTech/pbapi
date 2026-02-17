from datetime import datetime
from typing import List
from uuid import UUID

from src.schemas.common import CountryCode, CurrencyCode
from src.schemas.purchased_item import PurchasedItem
from src.schemas.receipt import Receipt


class SfsMdReceipt(Receipt):
    id: str | None = None
    date: datetime
    user_id: UUID
    company_id: str
    company_name: str
    country_code: CountryCode = CountryCode.MOLDOVA
    shop_address: str
    cash_register_id: str
    key: int
    currency_code: CurrencyCode = CurrencyCode.MOLDOVAN_LEU
    total_amount: float
    purchases: List[PurchasedItem]
    receipt_url: str
    receipt_canonical_url: str | None = None
    shop_id: int | None = None

    def model_post_init(self, __context) -> None:
        self.id = f"{CountryCode.MOLDOVA}_{self.cash_register_id}_{self.key}".lower()
        self.receipt_canonical_url = (
            f"https://mev.sfs.md/receipt-verifier/{self.cash_register_id}/"
            f"{self.total_amount:.2f}/{self.key}/{self.date:%Y-%m-%d}"
        )
