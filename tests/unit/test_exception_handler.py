from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.exception_handler import ExceptionHandler


class TestExceptionHandler:
    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        return request

    @pytest.fixture
    def mock_logger(self):
        logger = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_with_string_msg(
        self, mock_request, mock_logger
    ):
        exc = RequestValidationError(
            errors=[{"msg": "field required", "type": "value_error.missing"}]
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"code":"validation_error","message":"Validation error"}'
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_with_exception_msg(
        self, mock_request, mock_logger
    ):
        custom_error = ValueError("Invalid value")
        exc = RequestValidationError(
            errors=[{"msg": custom_error, "type": "value_error"}]
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"code":"validation_error","message":"Validation error"}'
        mock_logger.error.assert_called_once_with("Invalid value")

    @pytest.mark.asyncio
    async def test_request_validation_exception_handler_multiple_errors(
        self, mock_request, mock_logger
    ):
        exc = RequestValidationError(
            errors=[
                {"msg": "field required", "type": "value_error.missing"},
                {"msg": "invalid format", "type": "value_error.format"},
            ]
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.request_validation_exception_handler(
                mock_request, exc
            )

        assert response.status_code == 422
        assert response.body == b'{"code":"validation_error","message":"Validation error"}'
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_string_detail(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(status_code=404, detail="Resource not found")

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        assert response.body == b'{"code":"http_error","message":"HTTP error"}'
        mock_logger.error.assert_called_once_with("Resource not found")

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_non_string_detail(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(status_code=400, detail={"error": "bad request"})

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 400
        assert response.body == b'{"code":"http_error","message":"HTTP error"}'
        mock_logger.error.assert_called_once_with({"error": "bad request"})

    @pytest.mark.asyncio
    async def test_http_exception_handler_unauthorized(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(status_code=401, detail="Unauthorized")

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body == b'{"code":"http_error","message":"HTTP error"}'

    @pytest.mark.asyncio
    async def test_http_exception_handler_forbidden(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(status_code=403, detail="Forbidden")

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 403
        assert response.body == b'{"code":"http_error","message":"HTTP error"}'

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_auth_code_not_authenticated(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(
            status_code=401,
            detail={"code": "not_authenticated", "message": "Not authenticated"}
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body == b'{"code":"not_authenticated","message":"Not authenticated"}'

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_auth_code_token_expired(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(
            status_code=401,
            detail={"code": "token_expired", "message": "Token has expired"}
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body == b'{"code":"token_expired","message":"Token has expired"}'

    @pytest.mark.asyncio
    async def test_http_exception_handler_with_auth_code_invalid_token(
        self, mock_request, mock_logger
    ):
        exc = HTTPException(
            status_code=401,
            detail={"code": "invalid_token", "message": "Invalid token"}
        )

        with patch("app.exception_handler.logger", mock_logger):
            response = await ExceptionHandler.http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body == b'{"code":"invalid_token","message":"Invalid token"}'

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler(self, mock_request, mock_logger):
        exc = ValueError("Something went wrong")

        with patch("app.exception_handler.logger", mock_logger):
            with patch("app.exception_handler.exc_info", return_value=(None, exc, None)):
                response = await ExceptionHandler.unhandled_exception_handler(
                    mock_request, exc
                )

        assert response.status_code == 500
        assert response.body == b'{"code":"internal_error","message":"Internal server error"}'
        mock_logger.error.assert_called_once_with("Something went wrong")

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_with_different_exceptions(
        self, mock_request, mock_logger
    ):
        exceptions = [
            RuntimeError("Runtime error occurred"),
            KeyError("missing_key"),
            AttributeError("object has no attribute"),
            TypeError("wrong type"),
        ]

        for exc in exceptions:
            with patch("app.exception_handler.logger", mock_logger):
                with patch("app.exception_handler.exc_info", return_value=(None, exc, None)):
                    response = await ExceptionHandler.unhandled_exception_handler(
                        mock_request, exc
                    )

            assert response.status_code == 500
            assert response.body == b'{"code":"internal_error","message":"Internal server error"}'
            mock_logger.error.reset_mock()
