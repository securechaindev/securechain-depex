from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class SMTTimeoutException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=507,
            detail={"code": ResponseCode.SMT_TIMEOUT, "message": ResponseMessage.SMT_TIMEOUT}
        )
