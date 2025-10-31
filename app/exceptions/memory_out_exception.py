from fastapi import HTTPException


class MemoryOutException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=507,
            detail={"code": "memory_out", "message": "Memory exhausted or query timeout"}
        )
