from fastapi import HTTPException


class InvalidRepositoryException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, code="repository_not_found")


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, code="not_authenticated")


class ExpiredTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, code="token_expired")


class InvalidTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, code="invalid_token")


class MemoryOutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=507, code="memory_out")


class SMTTimeoutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=507, code="smt_timeout")
