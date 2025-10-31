from fastapi import HTTPException


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail={"code": "not_authenticated", "message": "Not authenticated"}
        )
