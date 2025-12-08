from sys import exc_info

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.constants import ResponseCode, ResponseMessage
from app.logger import logger


class ExceptionHandler:
    @staticmethod
    async def request_validation_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        if isinstance(exc, RequestValidationError):
            for error in exc.errors():
                msg = error["msg"]
                if isinstance(msg, Exception):
                    msg = str(msg)
            detail = {
                "code": ResponseCode.VALIDATION_ERROR,
                "message": msg,
            }
            logger.error(msg)
            return JSONResponse(status_code=422, content=detail)
        detail = {
            "code": ResponseCode.INTERNAL_ERROR,
            "message": ResponseMessage.INTERNAL_ERROR,
        }
        logger.error(str(exc))
        return JSONResponse(status_code=500, content=detail)

    @staticmethod
    async def http_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse | Response:
        if isinstance(exc, HTTPException):
            if isinstance(exc.detail, dict) and "code" in exc.detail:
                detail = exc.detail
            else:
                detail = {
                    "code": ResponseCode.HTTP_ERROR,
                    "message": ResponseMessage.HTTP_ERROR,
                }
            logger.error(exc.detail)
            return JSONResponse(status_code=exc.status_code, content=detail)
        detail = {
            "code": ResponseCode.INTERNAL_ERROR,
            "message": ResponseMessage.INTERNAL_ERROR,
        }
        logger.error(str(exc))
        return JSONResponse(status_code=500, content=detail)

    @staticmethod
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _, exception_value, _ = exc_info()
        detail = {
            "code": ResponseCode.INTERNAL_ERROR,
            "message": ResponseMessage.INTERNAL_ERROR,
        }
        logger.error(str(exception_value))
        return JSONResponse(status_code=500, content=detail)
