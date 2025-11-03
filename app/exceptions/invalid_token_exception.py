from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class InvalidTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail={"code": ResponseCode.INVALID_TOKEN, "message": ResponseMessage.INVALID_TOKEN}
        )
