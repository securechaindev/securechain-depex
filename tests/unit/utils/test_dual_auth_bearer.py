from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from app.exceptions import (
    ExpiredTokenException,
    InvalidTokenException,
    NotAuthenticatedException,
)
from app.utils import ApiKeyBearer, DualAuthBearer, JWTBearer


class TestDualAuthBearer:
    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.headers = {}
        request.cookies = {}
        return request

    @pytest.mark.asyncio
    async def test_api_key_takes_priority_over_jwt(self, mock_request):
        mock_request.headers = {"X-API-Key": "sk_test_key"}
        mock_request.cookies = {"access_token": "valid_jwt_token"}

        with patch.object(ApiKeyBearer, "__call__", new_callable=AsyncMock, return_value={"user_id": "api_key_user"}):
            dual_auth_bearer = DualAuthBearer()
            result = await dual_auth_bearer(mock_request)
            assert result == {"user_id": "api_key_user"}

    @pytest.mark.asyncio
    async def test_jwt_fallback_when_no_api_key(self, mock_request):
        mock_request.headers = {}
        mock_request.cookies = {"access_token": "valid_jwt_token"}

        with patch.object(JWTBearer, "__call__", return_value={"user_id": "jwt_user", "email": "user@example.com"}):
            dual_auth_bearer = DualAuthBearer()
            result = await dual_auth_bearer(mock_request)
            assert result == {"user_id": "jwt_user", "email": "user@example.com"}

    @pytest.mark.asyncio
    async def test_raises_not_authenticated_when_no_credentials(self, mock_request):
        mock_request.headers = {}
        mock_request.cookies = {}

        dual_auth_bearer = DualAuthBearer()
        with pytest.raises(NotAuthenticatedException):
            await dual_auth_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_raises_invalid_token_for_invalid_api_key(self, mock_request):
        mock_request.headers = {"X-API-Key": "invalid_key"}
        mock_request.cookies = {}

        dual_auth_bearer = DualAuthBearer()
        with pytest.raises(InvalidTokenException):
            await dual_auth_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_raises_expired_token_for_expired_jwt(self, mock_request):
        mock_request.headers = {}
        mock_request.cookies = {"access_token": "expired_jwt_token"}

        with patch.object(JWTBearer, "__call__", side_effect=ExpiredTokenException()):
            dual_auth_bearer = DualAuthBearer()
            with pytest.raises(ExpiredTokenException):
                await dual_auth_bearer(mock_request)

    @pytest.mark.asyncio
    async def test_api_key_header_is_detected(self, mock_request):
        mock_request.headers = {"X-API-Key": "sk_test"}

        with patch.object(ApiKeyBearer, "__call__", new_callable=AsyncMock, return_value={"user_id": "test"}) as mock_api_key:
            dual_auth_bearer = DualAuthBearer()
            await dual_auth_bearer(mock_request)
            mock_api_key.assert_called_once()

    def test_initialization_with_default_cookie_name(self):
        bearer = DualAuthBearer()
        assert bearer.jwt_bearer.cookie_name == "access_token"

    def test_initialization_with_custom_cookie_name(self):
        bearer = DualAuthBearer(cookie_name="custom_token")
        assert bearer.jwt_bearer.cookie_name == "custom_token"

    @pytest.mark.asyncio
    async def test_empty_api_key_header_falls_back_to_jwt(self, mock_request):
        mock_request.headers = {"X-API-Key": ""}
        mock_request.cookies = {"access_token": "valid_jwt_token"}

        with patch.object(JWTBearer, "__call__", return_value={"user_id": "jwt_user"}):
            dual_auth_bearer = DualAuthBearer()
            result = await dual_auth_bearer(mock_request)
            assert result == {"user_id": "jwt_user"}
