from datetime import datetime, timezone
from uuid import UUID

from src.schemas.common import QuantityUnit
from src.schemas.purchased_item import PurchasedItem
from src.schemas.sfs_md.receipt import SfsMdReceipt


def make_receipt():
	return SfsMdReceipt(
		date=datetime(2026, 2, 14, tzinfo=timezone.utc),
		user_id=UUID("12345678-1234-5678-1234-567812345678"),
		company_id="cmp_1",
		company_name="Test Co",
		shop_address="123 Test Street",
		cash_register_id="cr_1",
		key=42,
		total_amount=12.34,
		purchases=[
			PurchasedItem(
				name="Item A",
				quantity=2.0,
				unit=QuantityUnit.PIECE,
				price=6.17,
			)
		],
		receipt_url="https://example.com/receipt/42",
	)
