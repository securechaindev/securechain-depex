from typing import Any

from fastapi import HTTPException, Request, status
from jwt import ExpiredSignatureError, InvalidTokenError, decode

from app.config import settings


class JWTBearer:
    def __init__(self, cookie_name: str = "access_token"):
        self.cookie_name = cookie_name

    async def __call__(self, request: Request) -> dict[str, Any]:
        token = request.cookies.get(self.cookie_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = decode(
                token,
                settings.JWT_ACCESS_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            ) from err
        except InvalidTokenError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from err
        return payload
