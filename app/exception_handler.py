from sys import exc_info

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.logger import logger


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    for error in exc.errors():
        msg = error["msg"]
        if isinstance(msg, Exception):
            msg = str(msg)
    detail = {
        "code": "validation_error",
        "message": msg,
        "path": request.url.path
    }
    logger.info(detail)
    return JSONResponse(status_code=422, content=detail)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse | Response:
    detail = {
        "code": "http_error",
        "message": exc.detail,
        "path": request.url.path
    }
    logger.warning(detail)
    return JSONResponse(status_code=exc.status_code, content=detail)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
    _, exception_value, _ = exc_info()
    detail = {
        "code": "internal_error",
        "message": str(exception_value),
        "path": url
    }
    logger.error(detail)
    return JSONResponse(status_code=500, content=detail)
