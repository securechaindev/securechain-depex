from pydantic import BaseModel, Field


class VerifyAccessTokenRequest(BaseModel):
    access_token: str | None = Field(...)
