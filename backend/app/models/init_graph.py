from pydantic import BaseModel, Field


class InitGraphRequest(BaseModel):
    owner: str  = Field(...)
    name: str = Field(...)
    user_id: str = Field(...)
