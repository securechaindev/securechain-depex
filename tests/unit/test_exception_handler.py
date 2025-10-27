"""Unit tests for exception_handler module."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.exception_handler import ExceptionHandler


class TestExceptionHandler:
    """Test suite for ExceptionHandler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        return request

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_with_string_msg(
        self, mock_request, mock_logger
    ):
        """Test request_validation_exception_handler with string error message."""
        # Create a validation error with string message
        exc = RequestValidationError(
            errors=[{"msg": "field required", "type": "value_error.missing"}]
        )

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"detail":"validation_error"}'
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_with_exception_msg(
        self, mock_request, mock_logger
    ):
        """Test request_validation_exception_handler with Exception as message."""
        # Create a validation error with Exception object as message
        custom_error = ValueError("Invalid value")
        exc = RequestValidationError(
            errors=[{"msg": custom_error, "type": "value_error"}]
        )

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"detail":"validation_error"}'
        mock_logger.error.assert_called_once_with("Invalid value")

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_multiple_errors(
        self, mock_request, mock_logger
    ):
        """Test request_validation_exception_handler with multiple errors."""
        exc = RequestValidationError(
            errors=[
                {"msg": "field required", "type": "value_error.missing"},
                {"msg": "invalid format", "type": "value_error.format"},
            ]
        )

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"detail":"validation_error"}'
        # Should log the last error message
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_string_detail(
        self, mock_request, mock_logger
    ):
        """Test http_exception_handler with string detail."""
        exc = HTTPException(status_code=404, detail="Resource not found")

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        assert response.body == b'{"detail":"Resource not found"}'
        mock_logger.error.assert_called_once_with("Resource not found")

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_non_string_detail(
        self, mock_request, mock_logger
    ):
        """Test http_exception_handler with non-string detail."""
        exc = HTTPException(status_code=400, detail={"error": "bad request"})

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 400
        assert response.body == b'{"detail":"http_error"}'
        mock_logger.error.assert_called_once_with({"error": "bad request"})

    @pytest.mark.asyncio
    async def test_http_exception_handler_unauthorized(
        self, mock_request, mock_logger
    ):
        """Test http_exception_handler with 401 status."""
        exc = HTTPException(status_code=401, detail="Unauthorized")

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body == b'{"detail":"Unauthorized"}'

    @pytest.mark.asyncio
    async def test_http_exception_handler_forbidden(
        self, mock_request, mock_logger
    ):
        """Test http_exception_handler with 403 status."""
        exc = HTTPException(status_code=403, detail="Forbidden")

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 403
        assert response.body == b'{"detail":"Forbidden"}'

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler(self, mock_request, mock_logger):
        """Test unhandled_exception_handler."""
        exc = ValueError("Something went wrong")

        with patch("app.exception_handler.get_logger", return_value=mock_logger):
            with patch("app.exception_handler.exc_info", return_value=(None, exc, None)):
                response = await ExceptionHandler.unhandled_exception_handler(
                    mock_request, exc
                )

        assert response.status_code == 500
        assert response.body == b'{"detail":"internal_error"}'
        mock_logger.error.assert_called_once_with("Something went wrong")

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_with_different_exceptions(
        self, mock_request, mock_logger
    ):
        """Test unhandled_exception_handler with various exception types."""
        exceptions = [
            RuntimeError("Runtime error occurred"),
            KeyError("missing_key"),
            AttributeError("object has no attribute"),
            TypeError("wrong type"),
        ]

        for exc in exceptions:
            with patch("app.exception_handler.get_logger", return_value=mock_logger):
                with patch("app.exception_handler.exc_info", return_value=(None, exc, None)):
                    response = await ExceptionHandler.unhandled_exception_handler(
                        mock_request, exc
                    )

            assert response.status_code == 500
            assert response.body == b'{"detail":"internal_error"}'
            mock_logger.error.reset_mock()
