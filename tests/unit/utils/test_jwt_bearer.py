"""Tests for JWTBearer authentication."""

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

# Test constants
TEST_SECRET_KEY = "test-secret-key-for-testing-12345"
TEST_ALGORITHM = "HS256"


class TestJWTBearer:
    """Test suite for JWTBearer class."""

    @pytest.fixture
    def jwt_bearer(self):
        """Create JWTBearer instance."""
        return JWTBearer()

    @pytest.fixture
    def jwt_bearer_custom_cookie(self):
        """Create JWTBearer with custom cookie name."""
        return JWTBearer(cookie_name="custom_token")

    @pytest.fixture
    def valid_token(self):
        """Generate a valid JWT token."""
        payload = {"sub": "user123", "role": "admin"}
        return encode(
            payload,
            TEST_SECRET_KEY,
            algorithm=TEST_ALGORITHM,
        )

    @pytest.fixture
    def expired_token(self):
        """Generate an expired JWT token."""
        import time
        payload = {"sub": "user123", "exp": int(time.time()) - 3600}  # Expired 1 hour ago
        return encode(
            payload,
            TEST_SECRET_KEY,
            algorithm=TEST_ALGORITHM,
        )

    @pytest.fixture
    def invalid_token(self):
        """Generate an invalid JWT token with wrong secret."""
        payload = {"sub": "user123", "role": "admin"}
        return encode(
            payload,
            "wrong-secret-key",
            algorithm=TEST_ALGORITHM,
        )

    def test_init_default_cookie_name(self, jwt_bearer):
        """Test JWTBearer initialization with default cookie name."""
        assert jwt_bearer.cookie_name == "access_token"
        assert jwt_bearer.auto_error is False

    def test_init_custom_cookie_name(self, jwt_bearer_custom_cookie):
        """Test JWTBearer initialization with custom cookie name."""
        assert jwt_bearer_custom_cookie.cookie_name == "custom_token"
        assert jwt_bearer_custom_cookie.auto_error is False

    def test_call_with_valid_token(self, jwt_bearer, valid_token):
        """Test __call__ with valid JWT token in cookies."""
        # Create mock request with token in cookies
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": valid_token}

        # Mock settings to use test values
        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY
            mock_settings.ALGORITHM = TEST_ALGORITHM

            # Call should return decoded payload
            payload = jwt_bearer(request)
            assert isinstance(payload, dict)
            assert payload["sub"] == "user123"
            assert payload["role"] == "admin"

    def test_call_with_custom_cookie_token(self, jwt_bearer_custom_cookie, valid_token):
        """Test __call__ with valid token in custom cookie name."""
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
        """Test __call__ raises NotAuthenticatedException when no token in cookies."""
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
        """Test __call__ raises ExpiredTokenException with expired token."""
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
        """Test __call__ raises InvalidTokenException with invalid token."""
        request = Request(
            {
                "type": "http",
                "headers": [],
                "query_string": b"",
            }
        )
        request._cookies = {"access_token": invalid_token}

        with patch("app.utils.jwt_bearer.settings") as mock_settings:
            mock_settings.JWT_ACCESS_SECRET_KEY = TEST_SECRET_KEY  # Different from token secret
            mock_settings.ALGORITHM = TEST_ALGORITHM

            with pytest.raises(InvalidTokenException):
                jwt_bearer(request)

    def test_call_with_malformed_token_raises_invalid_token(self, jwt_bearer):
        """Test __call__ raises InvalidTokenException with malformed token."""
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
        """Test that exceptions preserve the original JWT exception in chain."""
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

            # Verify exception chaining
            assert exc_info.value.__cause__ is not None
