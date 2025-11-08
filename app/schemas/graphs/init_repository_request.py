from pydantic import BaseModel, Field


class InitRepositoryRequest(BaseModel):
    owner: str = Field(...)
    name: str = Field(...)
