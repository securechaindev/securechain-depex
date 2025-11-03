from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class ExpiredTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail={"code": ResponseCode.TOKEN_EXPIRED, "message": ResponseMessage.TOKEN_EXPIRED}
        )
