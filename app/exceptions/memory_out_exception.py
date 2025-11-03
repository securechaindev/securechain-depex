from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class MemoryOutException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=507,
            detail={"code": ResponseCode.MEMORY_OUT, "message": ResponseMessage.MEMORY_OUT}
        )
