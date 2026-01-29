import logging
import os
import unittest
import uuid
from datetime import datetime

from src.handlers.user_identity import UserIdentityHandler
from src.schemas.common import TableName
from src.schemas.user_identity import UserIdentity, IdentityProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")


class TestUserIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("ENV_NAME", "test")
        os.environ.setdefault("POSTGRES_HOST", "localhost")
        os.environ.setdefault("POSTGRES_PORT", "5433")
        os.environ.setdefault("POSTGRES_DB", "pbapi_test")
        os.environ.setdefault("POSTGRES_USER", "postgres")
        os.environ.setdefault("POSTGRES_PASSWORD", "postgres")

    def setUp(self):
        self.handler = UserIdentityHandler(logger)

    def _create_test_user(self):
        user_uuid = uuid.uuid4()
        user_data = {
            "id": str(user_uuid),
            "email": f"test-{user_uuid}@example.com",
            "name": "Test User",
            "creation_time": int(datetime.now().timestamp()),
            "login_generation": 1,
            "banned": False,
        }
        self.handler.db.use_table(TableName.USER)
        self.handler.db.create_one(user_data)
        return user_uuid

    def test_create_and_find_identity(self):
        user_id = self._create_test_user()
        identity_id = f"test-id-{uuid.uuid4()}"

        # 1. Create
        identity = UserIdentity(
            id=identity_id, provider=IdentityProvider.GOOGLE, user_id=user_id
        )
        created_id = self.handler.create(identity)
        self.assertEqual(created_id, identity_id)

        # 2. Find
        found = self.handler.find(identity_id, IdentityProvider.GOOGLE)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, identity_id)
        self.assertEqual(found.user_id, user_id)

    def test_update_identity(self):
        user_id = self._create_test_user()
        identity_id = f"test-id-{uuid.uuid4()}"
        identity = UserIdentity(
            id=identity_id, provider=IdentityProvider.GOOGLE, user_id=user_id
        )
        self.handler.create(identity)

        found = self.handler.find(identity_id, IdentityProvider.GOOGLE)
        self.assertIsNotNone(found)

        # Update (same value or just test update call)
        found.provider = IdentityProvider.GOOGLE
        updated = self.handler.update(found)
        self.assertTrue(updated)

        # Verify Update
        verified = self.handler.find(identity_id, IdentityProvider.GOOGLE)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.user_id, user_id)

    def test_get_or_create_user_by_identity_existing(self):
        user_id = self._create_test_user()
        user_uuid_str = str(user_id)
        email = f"test-{user_id}@example.com"
        identity_id = f"test-id-{uuid.uuid4()}"

        identity = UserIdentity(
            id=identity_id, provider=IdentityProvider.GOOGLE, user_id=user_id
        )
        self.handler.create(identity)

        user = self.handler.get_or_create_user_by_identity(
            identity_id, IdentityProvider.GOOGLE, email, "Test User"
        )
        self.assertEqual(str(user.id), user_uuid_str)
        self.assertEqual(user.email, email)

    def test_get_or_create_user_by_identity_new(self):
        new_identity_id = f"new-id-{uuid.uuid4()}"
        new_email = f"new-{uuid.uuid4()}@example.com"

        new_user = self.handler.get_or_create_user_by_identity(
            new_identity_id, IdentityProvider.GOOGLE, new_email, "New User"
        )
        self.assertEqual(new_user.email, new_email)
        self.assertEqual(new_user.name, "New User")

        # Verify it was actually created in DB
        found_identity = self.handler.find(new_identity_id, IdentityProvider.GOOGLE)
        self.assertIsNotNone(found_identity)
        self.assertEqual(str(found_identity.user_id), str(new_user.id))

    def test_get_or_create_user_by_identity_no_email(self):
        new_identity_id = f"no-email-id-{uuid.uuid4()}"

        new_user = self.handler.get_or_create_user_by_identity(
            new_identity_id, IdentityProvider.TELEGRAM, None, "Telegram User"
        )
        self.assertIsNone(new_user.email)
        self.assertEqual(new_user.name, "Telegram User")

        # Verify it was actually created in DB
        found_identity = self.handler.find(new_identity_id, IdentityProvider.TELEGRAM)
        self.assertIsNotNone(found_identity)
        self.assertEqual(str(found_identity.user_id), str(new_user.id))
