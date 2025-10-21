from fastapi import HTTPException


class InvalidRepositoryException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="repository_not_found")
