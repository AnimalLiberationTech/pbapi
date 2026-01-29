from typing import Optional
from uuid import UUID

from pydantic import EmailStr

from src.adapters.db.postgresql import PostgreSQLAdapter, init_db_session
from src.schemas.common import TableName
from src.schemas.user import User
from src.schemas.user_identity import UserIdentity, IdentityProvider


class UserIdentityHandler:
    def __init__(self, logger):
        self.logger = logger
        self.db: PostgreSQLAdapter = init_db_session(self.logger)

    def find(self, identity_id: str, provider: str) -> Optional[UserIdentity]:
        """
        Find a UserIdentity by its id and provider.
        """
        self.logger.info(
            f"Finding user identity: {identity_id} for provider: {provider}"
        )

        self.db.use_table(TableName.USER_IDENTITY)
        data = self.db.read_one(identity_id)

        if not data:
            return None

        # Verify provider if specified
        if data.get("provider") != provider:
            self.logger.warning(
                f"Found identity {identity_id} but provider mismatch: {data.get('provider')} != {provider}"
            )
            return None

        return UserIdentity(**data)

    def create(self, identity: UserIdentity) -> str:
        """
        Create a new UserIdentity.
        """
        self.logger.info(
            f"Creating user identity: {identity.id} for provider: {identity.provider}"
        )

        self.db.use_table(TableName.USER_IDENTITY)
        data = identity.model_dump(mode="json")
        return self.db.create_one(data)

    def update(self, identity: UserIdentity) -> bool:
        """
        Update an existing UserIdentity.
        """
        self.logger.info(f"Updating user identity: {identity.id}")

        self.db.use_table(TableName.USER_IDENTITY)
        data = identity.model_dump(mode="json")
        identity_id = data.pop("id")
        return self.db.update_one(identity_id, data)

    def get_or_create_user_by_identity(
        self, _id: str, provider: str, email: Optional[EmailStr], name: str
    ) -> User:
        identity = self.find(_id, provider)

        if identity:
            self.logger.info(f"Found existing identity for user: {identity.user_id}")

            self.db.use_table(TableName.USER)
            return User(**self.db.read_one(str(identity.user_id)))

        self.logger.info(f"Identity not found. Creating new user for {provider} id {_id}")

        self.db.use_table(TableName.USER)
        new_user = User(email=email, name=name)
        user_id = self.db.create_one(new_user.model_dump(mode="json"))
        new_user.id = UUID(user_id)

        self.logger.info(f"Creating new identity for user: {user_id}")
        new_identity = UserIdentity(
            id=_id, provider=IdentityProvider(provider), user_id=UUID(user_id)
        )
        self.create(new_identity)

        return new_user
