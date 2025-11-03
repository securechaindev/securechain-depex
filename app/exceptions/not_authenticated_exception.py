from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail={"code": ResponseCode.NOT_AUTHENTICATED, "message": ResponseMessage.NOT_AUTHENTICATED}
        )
