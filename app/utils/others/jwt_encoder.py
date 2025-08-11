# security.py
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from jwt import decode, ExpiredSignatureError, InvalidTokenError

from app.config import settings


class JWTBearer:
    def __init__(self, cookie_name: str = "access_token"):
        self.cookie_name = cookie_name

    async def __call__(self, request: Request) -> Dict[str, Any]:
        token = request.cookies.get(self.cookie_name)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = decode(
                token,
                settings.JWT_ACCESS_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return payload
