from datetime import datetime, timedelta

from jose import jwt
from jwt.exceptions import InvalidTokenError

from app.config import settings


async def create_access_token(subject: str, expires_delta: int | None = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now() + expires_delta
    else:
        expires_delta = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(access_token: str) -> bool:
    try:
        jwt.decode(access_token, settings.JWT_SECRET_KEY, settings.ALGORITHM)
        return True
    except InvalidTokenError:
        return False
