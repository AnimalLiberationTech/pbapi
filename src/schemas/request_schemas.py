from typing import Optional

from pydantic import BaseModel, EmailStr

from src.schemas.sfs_md.receipt import SfsMdReceipt
from src.schemas.user_identity import IdentityProvider


class GetReceiptByUrlRequest(BaseModel):
    url: str


class LinkShopRequest(BaseModel):
    shop_id: int
    receipt: SfsMdReceipt


class AddBarcodesRequest(BaseModel):
    shop_id: str
    items: list


class GetOrCreateUserByIdentityRequest(BaseModel):
    id: str
    provider: IdentityProvider
    email: Optional[EmailStr] = None
    name: str
