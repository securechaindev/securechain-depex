from typing import Any

from fastapi import Request
from fastapi.security import HTTPBearer

from app.utils.api_key_bearer import ApiKeyBearer
from app.utils.jwt_bearer import JWTBearer


class DualAuthBearer(HTTPBearer):
    def __init__(self, cookie_name: str = "access_token"):
        super().__init__(auto_error=False)
        self.jwt_bearer = JWTBearer(cookie_name=cookie_name)
        self.api_key_bearer = ApiKeyBearer(auto_error=False)

    async def __call__(self, request: Request) -> dict[str, Any]:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self.api_key_bearer(request)
        return self.jwt_bearer(request)
