from typing import Any

from fastapi import Request
from fastapi.security import HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError, decode

from app.exceptions import (
    ExpiredTokenException,
    InvalidTokenException,
    NotAuthenticatedException,
)
from app.settings import settings


class JWTBearer(HTTPBearer):
    def __init__(self, cookie_name: str = "access_token"):
        super().__init__(auto_error=False)
        self.cookie_name = cookie_name

    def __call__(self, request: Request) -> dict[str, Any]:
        token = request.cookies.get(self.cookie_name)
        if not token:
            raise NotAuthenticatedException()
        try:
            payload = decode(
                token,
                settings.JWT_ACCESS_SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except ExpiredSignatureError as err:
            raise ExpiredTokenException() from err
        except InvalidTokenError as err:
            raise InvalidTokenException() from err
        return payload
