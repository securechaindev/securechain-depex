from datetime import datetime

from pydantic import BaseModel, Field


class ApiKey(BaseModel):
    key_hash: str
    user_id: str
    name: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    is_active: bool = True
