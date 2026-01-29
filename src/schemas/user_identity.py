from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from src.schemas.schema_base import SchemaBase


class IdentityProvider(StrEnum):
    GOOGLE = "google"
    TELEGRAM = "telegram"
    APPWRITE = "appwrite"
    SUPABASE = "supabase"

    @classmethod
    def get(cls, value):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} does not exist in {cls.__name__}")


class UserIdentity(SchemaBase):
    id: str
    provider: IdentityProvider
    user_id: UUID
    created_at: datetime = datetime.now(tz=timezone.utc)
