from pydantic import BaseModel, Field, validator

from app.models.patterns import NEO4J_ID_PATTERN
from app.models.validators import validate_max_level


class FileInfoRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_level: int = Field(...)

    @validator("max_level")
    def validate_max_level(cls, value):
        return validate_max_level(value)
