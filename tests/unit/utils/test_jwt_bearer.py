
from unittest.mock import patch

import pytest
from fastapi import Request
from jwt import encode

from app.exceptions import (
    ExpiredTokenException,
    InvalidTokenException,
    NotAuthenticatedException,
)
from app.utils.jwt_bearer import JWTBearer

TEST_SECRET_KEY = "test-secret-key-for-testing-12345"
TEST_ALGORITHM = "HS256"


class TestJWTBearer:

    @pytest.fixture
    def jwt_bearer(self):
        return JWTBearer()

    @pytest.fixture
    def jwt_bearer_custom_cookie(self):
        return JWTBearer(cookie_name="custom_token")

    @pytest.fixture
    def valid_token(self):
        payload = {"sub": "user123", "role": "admin"}
        return encode(
            payload,
            TEST_SECRET_KEY,
            algorithm=TEST_ALGORITHM,
        )

    @pytest.fixture
    def expired_token(self):
        import time
        payload = {"sub": "user123", "exp": int(time.time()) - 3600}
        return encode(
            payload,
            TEST_SECRET_KEY,
            algorithm=TEST_ALGORITHM,
        )

    @pytest.fixture
    def invalid_token(self):
        payload = {"sub": "user123", "role": "admin"}
        return encode(
            payload,
            "wrong-secret-key",
            algorithm=TEST_ALGORITHM,
        )

    def test_init_default_cookie_name(self, jwt_bearer):
        assert jwt_bearer.cookie_name == "access_token"
        assert jwt_bearer.auto_error is False

    def test_init_custom_cookie_name(self, jwt_bearer_custom_cookie):
        assert jwt_bearer_custom_cookie.cookie_name == "custom_token"
        assert jwt_bearer_custom_cookie.auto_error is False

    def test_call_with_valid_token(self, jwt_bearer, valid_token):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": valid_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            payload = jwt_bearer(request)
            assert isinstance(payload, dict)
            assert payload["sub"] == "user123"
            assert payload["role"] == "admin"

    def test_call_with_custom_cookie_token(self, jwt_bearer_custom_cookie, valid_token):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"custom_token": valid_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            payload = jwt_bearer_custom_cookie(request)
            assert isinstance(payload, dict)
            assert payload["sub"] == "user123"

    def test_call_without_token_raises_not_authenticated(self, jwt_bearer):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {}

        with pytest.raises(NotAuthenticatedException):
            jwt_bearer(request)

    def test_call_with_expired_token_raises_expired_token(self, jwt_bearer, expired_token):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": expired_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            with pytest.raises(ExpiredTokenException):
                jwt_bearer(request)

    def test_call_with_invalid_token_raises_invalid_token(self, jwt_bearer, invalid_token):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": invalid_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            with pytest.raises(InvalidTokenException):
                jwt_bearer(request)

    def test_call_with_malformed_token_raises_invalid_token(self, jwt_bearer):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": "malformed.token.here"}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            with pytest.raises(InvalidTokenException):
                jwt_bearer(request)

    def test_call_preserves_exception_chain(self, jwt_bearer, expired_token):
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": expired_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            with pytest.raises(ExpiredTokenException) as exc_info:
                jwt_bearer(request)

            assert exc_info.value.__cause__ is not None
