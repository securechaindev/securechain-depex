from fastapi import HTTPException


class MemoryOutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=507, detail="memory_out")
