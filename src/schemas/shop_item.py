from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

from src.helpers.common import validate_barcode
from src.schemas.common import ItemBarcodeStatus
from src.schemas.schema_base import SchemaBase


# there could be more than one item with the same name in the same shop
class ShopItem(SchemaBase):
    id: Optional[UUID] = Field(default_factory=uuid4)
    shop_id: int
    name: str
    status: ItemBarcodeStatus
    barcode: str | None = None

    def model_post_init(self, __context) -> None:
        if self.status == ItemBarcodeStatus.ADDED:
            if not self.barcode:
                raise ValueError("Barcode must be provided for added items")

            self.barcode = self.barcode.strip().replace(" ", "")
            if not validate_barcode(self.barcode):
                raise ValueError("Invalid barcode")
