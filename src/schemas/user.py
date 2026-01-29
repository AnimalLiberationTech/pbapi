from datetime import datetime, date, timezone
from enum import StrEnum, IntEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field, EmailStr, field_validator

from src.schemas.schema_base import SchemaBase


class UserRightsGroup(StrEnum):
    NORMAL = "normal"
    TESTER = "tester"
    CONTENT_MODERATOR = "content_moderator"
    GLOBAL_MODERATOR = "everything_moderator"
    ADMINISTRATOR = "administrator"

    @classmethod
    def get(cls, value):
        if isinstance(value, int):
            # Map from UserRightsGroupCode
            for member in UserRightsGroupCode:
                if member.value == value:
                    return cls[member.name]
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} does not exist in {cls.__name__}")


class UserRightsGroupCode(IntEnum):
    NORMAL = 1
    TESTER = 2
    CONTENT_MODERATOR = 3
    GLOBAL_MODERATOR = 4
    ADMINISTRATOR = 5


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    TRANSGENDER = "transgender"
    NON_BINARY = "non-binary"
    OTHER = "other"

    @classmethod
    def get(cls, value):
        if isinstance(value, int):
            # Map from GenderCode
            for member in GenderCode:
                if member.value == value:
                    return cls[member.name]
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} does not exist in {cls.__name__}")


class GenderCode(IntEnum):
    MALE = 1
    FEMALE = 2
    TRANSGENDER = 3
    NON_BINARY = 4
    OTHER = 5


class User(SchemaBase):
    id: Optional[UUID] = Field(default_factory=uuid4)
    email: EmailStr | None = None
    name: str
    creation_time: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    login_generation: int = 1
    banned: bool = False
    self_description: str | None = None
    gender: Gender | None = None
    birthday: date | None = None
    user_rights_group: UserRightsGroup = UserRightsGroup.NORMAL
    avatar_id: UUID | None = None
    created_at: datetime = datetime.now(tz=timezone.utc)

    @field_validator("user_rights_group", mode="before")
    @classmethod
    def validate_user_rights_group(cls, v):
        return UserRightsGroup.get(v)

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, v):
        if v is None:
            return None
        return Gender.get(v)

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if "user_rights_group" in data:
            data["user_rights_group"] = UserRightsGroupCode[
                UserRightsGroup(data["user_rights_group"]).name
            ].value
        if "gender" in data and data["gender"] is not None:
            data["gender"] = GenderCode[Gender(data["gender"]).name].value
        return data
