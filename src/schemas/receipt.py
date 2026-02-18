from datetime import datetime
from typing import List
from uuid import UUID

from src.schemas.common import CountryCode, CurrencyCode
from src.schemas.purchased_item import PurchasedItem
from src.schemas.schema_base import SchemaBase


class Receipt(SchemaBase):
    id: str
    date: datetime
    user_id: UUID
    company_id: str
    company_name: str
    country_code: CountryCode
    shop_address: str
    cash_register_id: str
    key: int | str
    currency_code: CurrencyCode
    total_amount: float
    purchases: List[PurchasedItem]
    receipt_url: str
    shop_id: int | None = None
