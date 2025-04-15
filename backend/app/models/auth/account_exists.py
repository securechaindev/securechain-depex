from pydantic import BaseModel, Field

from app.models.patterns import EMAIL_PATTERN


class AccountExistsRequest(BaseModel):
    email: str = Field(
        pattern=EMAIL_PATTERN
    )
