from sys import exc_info

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.logger import logger


class ExceptionHandler:
    @staticmethod
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        for error in exc.errors():
            msg = error["msg"]
            if isinstance(msg, Exception):
                msg = str(msg)
        detail = {
            "detail": "validation_error",
        }
        logger.error(msg)
        return JSONResponse(status_code=422, content=detail)

    @staticmethod
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse | Response:
        detail = {
            "detail": exc.detail if isinstance(exc.detail, str) else "http_error",
        }
        logger.error(exc.detail)
        return JSONResponse(status_code=exc.status_code, content=detail)

    @staticmethod
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        _, exception_value, _ = exc_info()
        detail = {
            "detail": "internal_error",
        }
        logger.error(str(exception_value))
        return JSONResponse(status_code=500, content=detail)
