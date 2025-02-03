from pydantic import BaseModel, Field, validator

from .patterns import EMAIL_PATTERN
from .validators import validate_password


class LoginRequest(BaseModel):
    email: str = Field(
        pattern=EMAIL_PATTERN
    )
    password: str = Field(...)

    @validator("password")
    def validate_password(cls, value):
        return validate_password(value)
