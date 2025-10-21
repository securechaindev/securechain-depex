from fastapi import HTTPException


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="not_authenticated")
