from pydantic import BaseModel, Field

from .patterns import EMAIL_PATTERN


class AccountExistsRequest(BaseModel):
    email: str = Field(
        pattern=EMAIL_PATTERN
    )
