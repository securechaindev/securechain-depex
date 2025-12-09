import hashlib

from fastapi import Request
from fastapi.security import HTTPBearer

from app.database import DatabaseManager
from app.exceptions import InvalidTokenException, NotAuthenticatedException
from app.models.api_key import ApiKey


class ApiKeyBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    @staticmethod
    def hash(api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def __call__(self, request: Request) -> dict[str, str] | None:
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            if self.auto_error:
                raise NotAuthenticatedException()
            return None

        if not api_key.startswith("sk_"):
            raise InvalidTokenException()

        key_hash = self.hash(api_key)

        db_manager = DatabaseManager()
        api_keys_collection = db_manager.get_api_keys_collection()

        stored_key_dict = await api_keys_collection.find_one({"key_hash": key_hash})

        if not stored_key_dict:
            raise InvalidTokenException()

        try:
            stored_key = ApiKey(**stored_key_dict)
        except Exception as err:
            raise InvalidTokenException() from err

        if not stored_key.is_active:
            raise InvalidTokenException()

        return {"user_id": stored_key.user_id}
