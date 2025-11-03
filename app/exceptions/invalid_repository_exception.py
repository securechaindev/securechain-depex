from fastapi import HTTPException

from app.constants import ResponseCode, ResponseMessage


class InvalidRepositoryException(HTTPException):
    def __init__(self, owner: str, name: str):
        super().__init__(
            status_code=404,
            detail={"code": ResponseCode.REPOSITORY_NOT_FOUND, "message": ResponseMessage.REPOSITORY_NOT_FOUND.format(name=name, owner=owner)}
        )
