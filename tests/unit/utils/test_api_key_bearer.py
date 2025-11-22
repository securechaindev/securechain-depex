from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from app.exceptions import InvalidTokenException, NotAuthenticatedException
from app.utils import ApiKeyBearer


class TestApiKeyBearer:
    @pytest.fixture
    def api_key_bearer(self):
        return ApiKeyBearer()

    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_valid_api_key(self, api_key_bearer, mock_request):
        mock_request.headers = {"X-API-Key": "sk_valid_key_123"}

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {
            "key_hash": api_key_bearer.hash("sk_valid_key_123"),
            "user_id": "user123",
            "is_active": True,
            "expires_at": datetime.now(UTC) + timedelta(days=30)
        }

        with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db_manager:
            mock_db_instance = MagicMock()
            mock_db_instance.get_api_keys_collection.return_value = mock_collection
            mock_db_manager.return_value = mock_db_instance

            result = await api_key_bearer(mock_request)

            assert result == {"user_id": "user123"}
            mock_collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_api_key(self, api_key_bearer, mock_request):
        mock_request.headers = {}

        with pytest.raises(NotAuthenticatedException):
            await api_key_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_invalid_api_key_format(self, api_key_bearer, mock_request):
        mock_request.headers = {"X-API-Key": "invalid_key_without_prefix"}

        with pytest.raises(InvalidTokenException):
            await api_key_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_nonexistent_api_key(self, api_key_bearer, mock_request):
        mock_request.headers = {"X-API-Key": "sk_nonexistent_key"}

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None

        with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db_manager:
            mock_db_instance = MagicMock()
            mock_db_instance.get_api_keys_collection.return_value = mock_collection
            mock_db_manager.return_value = mock_db_instance

            with pytest.raises(InvalidTokenException):
                await api_key_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_inactive_api_key(self, api_key_bearer, mock_request):
        mock_request.headers = {"X-API-Key": "sk_inactive_key"}

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {
            "key_hash": api_key_bearer.hash("sk_inactive_key"),
            "user_id": "user123",
            "is_active": False,
            "expires_at": datetime.now(UTC) + timedelta(days=30)
        }

        with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db_manager:
            mock_db_instance = MagicMock()
            mock_db_instance.get_api_keys_collection.return_value = mock_collection
            mock_db_manager.return_value = mock_db_instance

            with pytest.raises(InvalidTokenException):
                await api_key_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_api_key_without_expiration(self, api_key_bearer, mock_request):
        mock_request.headers = {"X-API-Key": "sk_no_expiration"}

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {
            "key_hash": api_key_bearer.hash("sk_no_expiration"),
            "user_id": "user456",
            "is_active": True,
            "expires_at": None
        }

        with patch("app.utils.api_key_bearer.DatabaseManager") as mock_db_manager:
            mock_db_instance = MagicMock()
            mock_db_instance.get_api_keys_collection.return_value = mock_collection
            mock_db_manager.return_value = mock_db_instance

            result = await api_key_bearer(mock_request)

            assert result == {"user_id": "user456"}

    def test_hash_function(self, api_key_bearer):
        api_key = "sk_test_key_123"
        hash1 = api_key_bearer.hash(api_key)
        hash2 = api_key_bearer.hash(api_key)

        assert hash1 == hash2
        assert len(hash1) == 64
