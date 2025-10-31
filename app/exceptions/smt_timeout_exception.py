from fastapi import HTTPException


class SMTTimeoutException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=507,
            detail={"code": "smt_timeout", "message": "SMT timeout occurred"}
        )
