from datetime import datetime
from pydantic import BaseModel, Field


class InitRepositoryRequest(BaseModel):
    owner: str  = Field(...)
    name: str = Field(...)
    moment: datetime = Field(default_factory=datetime.now)
    add_extras: bool = Field(default=False)
    is_complete: bool = Field(default=False)
    user_id: str = Field(...)
