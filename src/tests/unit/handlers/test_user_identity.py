from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from src.handlers.user_identity import UserIdentityHandler
from src.schemas.common import TableName
from src.schemas.user_identity import UserIdentity, IdentityProvider


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def user_identity_handler(mock_logger):
    with patch('src.handlers.user_identity.init_db_session') as mock_init:
        mock_init.return_value = Mock()
        handler = UserIdentityHandler(mock_logger)
        handler.db = Mock()
        return handler


class TestUserIdentityHandlerFind:
    def test_find_existing_identity(self, user_identity_handler):
        """Test finding an existing user identity"""
        identity_data = {
            'id': 'google_123',
            'provider': 'google',
            'user_id': UUID('12345678-1234-5678-1234-567812345678')
        }
        user_identity_handler.db.read_many.return_value = [identity_data]

        result = user_identity_handler.find('google_123', 'google')

        assert result is not None
        assert result.id == 'google_123'
        assert result.provider == 'google'
        user_identity_handler.db.use_table.assert_called_with(TableName.USER_IDENTITY)
        user_identity_handler.db.read_many.assert_called_with(
            {'id': 'google_123', 'provider': 'google'}, limit=1
        )

    def test_find_nonexistent_identity(self, user_identity_handler):
        """Test finding a non-existent user identity"""
        user_identity_handler.db.read_many.return_value = []

        result = user_identity_handler.find('nonexistent_id', 'provider')

        assert result is None
        user_identity_handler.db.use_table.assert_called_with(TableName.USER_IDENTITY)

    def test_find_logs_correctly(self, user_identity_handler, mock_logger):
        """Test that find method logs the attempt"""
        user_identity_handler.db.read_many.return_value = []

        user_identity_handler.find('test_id', 'test_provider')

        mock_logger.info.assert_called_with(
            f"Finding user identity: test_id for provider: test_provider"
        )


class TestUserIdentityHandlerCreate:
    def test_create_identity(self, user_identity_handler):
        """Test creating a new user identity"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity = UserIdentity(
            id='google_123',
            provider=IdentityProvider.GOOGLE,
            user_id=user_id
        )
        user_identity_handler.db.create_one.return_value = 'google_123'

        result = user_identity_handler.create(identity)

        assert result == 'google_123'
        user_identity_handler.db.use_table.assert_called_with(TableName.USER_IDENTITY)
        user_identity_handler.db.create_one.assert_called_once()

    def test_create_logs_correctly(self, user_identity_handler, mock_logger):
        """Test that create method logs correctly"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity = UserIdentity(
            id='google_123',
            provider=IdentityProvider.GOOGLE,
            user_id=user_id
        )
        user_identity_handler.db.create_one.return_value = 'google_123'

        user_identity_handler.create(identity)

        mock_logger.info.assert_called_with(
            f"Creating user identity: google_123 for provider: google"
        )


class TestUserIdentityHandlerUpdate:
    def test_update_identity(self, user_identity_handler):
        """Test updating an existing user identity"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity = UserIdentity(
            id='google_123',
            provider=IdentityProvider.GOOGLE,
            user_id=user_id
        )
        user_identity_handler.db.update_one_by.return_value = True

        result = user_identity_handler.update(identity)

        assert result is True
        user_identity_handler.db.use_table.assert_called_with(TableName.USER_IDENTITY)
        user_identity_handler.db.update_one_by.assert_called_once()

    def test_update_removes_id_and_provider_from_update_data(self, user_identity_handler):
        """Test that update removes id and provider from the update payload"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity = UserIdentity(
            id='google_123',
            provider=IdentityProvider.GOOGLE,
            user_id=user_id
        )
        user_identity_handler.db.update_one_by.return_value = True

        user_identity_handler.update(identity)

        # Verify that id and provider are not in the update data
        call_args = user_identity_handler.db.update_one_by.call_args
        update_data = call_args[0][1]
        assert 'id' not in update_data
        assert 'provider' not in update_data

    def test_update_failed(self, user_identity_handler):
        """Test updating when database update fails"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity = UserIdentity(
            id='google_123',
            provider=IdentityProvider.GOOGLE,
            user_id=user_id
        )
        user_identity_handler.db.update_one_by.return_value = False

        result = user_identity_handler.update(identity)

        assert result is False


class TestUserIdentityHandlerGetOrCreateUserByIdentity:
    def test_get_existing_user_by_identity(self, user_identity_handler):
        """Test getting an existing user via identity"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity_data = {
            'id': 'google_123',
            'provider': 'google',
            'user_id': user_id
        }
        user_data = {
            'id': str(user_id),
            'email': 'test@example.com',
            'name': 'Test User'
        }

        user_identity_handler.db.read_many.return_value = [identity_data]
        user_identity_handler.db.read_one.return_value = user_data

        result = user_identity_handler.get_or_create_user_by_identity(
            'google_123', 'google', 'test@example.com', 'Test User'
        )

        assert result.id == user_id
        assert result.email == 'test@example.com'
        assert result.name == 'Test User'
        user_identity_handler.db.read_many.assert_called_once()
        user_identity_handler.db.read_one.assert_called_once()
        user_identity_handler.db.create_one.assert_not_called()

    def test_create_new_user_when_identity_not_found(self, user_identity_handler):
        """Test creating a new user when identity doesn't exist"""
        new_user_id = '87654321-4321-8765-4321-876543218765'
        user_identity_handler.db.read_many.return_value = []
        user_identity_handler.db.create_one.side_effect = [new_user_id, 'google_123']

        result = user_identity_handler.get_or_create_user_by_identity(
            'google_123', 'google', 'newuser@example.com', 'New User'
        )

        assert result.email == 'newuser@example.com'
        assert result.name == 'New User'
        assert result.id == UUID(new_user_id)
        # Should call create_one twice: once for user, once for identity
        assert user_identity_handler.db.create_one.call_count == 2

    def test_create_new_user_with_none_email(self, user_identity_handler):
        """Test creating a new user with None email"""
        new_user_id = '87654321-4321-8765-4321-876543218765'
        user_identity_handler.db.read_many.return_value = []
        user_identity_handler.db.create_one.side_effect = [new_user_id, 'g_456']

        result = user_identity_handler.get_or_create_user_by_identity(
            'g_456', IdentityProvider.GOOGLE, None, 'Google User'
        )

        assert result.email is None
        assert result.name == 'Google User'

    def test_logs_found_identity(self, user_identity_handler, mock_logger):
        """Test logging when identity is found"""
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        identity_data = {
            'id': 'google_123',
            'provider': 'google',
            'user_id': user_id
        }
        user_data = {
            'id': str(user_id),
            'email': 'test@example.com',
            'name': 'Test User'
        }

        user_identity_handler.db.read_many.return_value = [identity_data]
        user_identity_handler.db.read_one.return_value = user_data

        user_identity_handler.get_or_create_user_by_identity(
            'google_123', 'google', 'test@example.com', 'Test User'
        )

        # Verify "Found existing identity" log
        assert any(
            "Found existing identity" in str(call)
            for call in mock_logger.info.call_args_list
        )

    def test_logs_new_identity_creation(self, user_identity_handler, mock_logger):
        """Test logging when creating a new identity"""
        new_user_id = '87654321-4321-8765-4321-876543218765'
        user_identity_handler.db.read_many.return_value = []
        user_identity_handler.db.create_one.side_effect = [new_user_id, 'google_123']

        user_identity_handler.get_or_create_user_by_identity(
            'google_123', 'google', 'newuser@example.com', 'New User'
        )

        # Verify logs
        assert any(
            "Identity not found" in str(call)
            for call in mock_logger.info.call_args_list
        )
        assert any(
            "Creating new identity" in str(call)
            for call in mock_logger.info.call_args_list
        )

    def test_uses_correct_table_names(self, user_identity_handler):
        """Test that the correct tables are used"""
        new_user_id = '87654321-4321-8765-4321-876543218765'
        user_identity_handler.db.read_many.return_value = []
        user_identity_handler.db.create_one.side_effect = [new_user_id, 'google_123']

        user_identity_handler.get_or_create_user_by_identity(
            'google_123', 'google', 'newuser@example.com', 'New User'
        )

        use_table_calls = [call[0][0] for call in user_identity_handler.db.use_table.call_args_list]
        assert TableName.USER_IDENTITY in use_table_calls
        assert TableName.USER in use_table_calls