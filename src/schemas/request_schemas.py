from typing import Optional
from pydantic import BaseModel, EmailStr


from src.schemas.user_identity import IdentityProvider


class ParseFromUrlRequest(BaseModel):
    url: str
    user_id: str


class LinkShopRequest(BaseModel):
    url: str
    user_id: str
    receipt_id: str


class AddBarcodesRequest(BaseModel):
    shop_id: str
    items: list


class GetOrCreateUserByIdentityRequest(BaseModel):
    id: str
    provider: IdentityProvider
    email: Optional[EmailStr] = None
    name: str
