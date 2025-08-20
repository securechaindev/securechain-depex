from fastapi import HTTPException


class InvalidRepositoryException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="repository_not_found")


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="not_authenticated")


class ExpiredTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="token_expired")


class InvalidTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="invalid_token")


class MemoryOutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=507, detail="memory_out")


class SMTTimeoutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=507, detail="smt_timeout")
