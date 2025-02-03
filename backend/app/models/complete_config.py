from pydantic import BaseModel, Field, validator

from .agregator import Agregator
from .manager import Manager
from .patterns import NEO4J_ID_PATTERN
from .validators import validate_max_level


class CompleteConfigRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_level: int = Field(...)
    manager: Manager
    agregator: Agregator
    config: dict[str, str]

    @validator("max_level")
    def validate_max_level(cls, value):
        return validate_max_level(value)
