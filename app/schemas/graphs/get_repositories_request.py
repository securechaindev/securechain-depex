from pydantic import BaseModel, Field

from app.schemas.patterns import MONGO_OBJECT_ID_PATTERN


class GetRepositoriesRequest(BaseModel):
    user_id: str  = Field(
        ...,
        pattern=MONGO_OBJECT_ID_PATTERN
    )
