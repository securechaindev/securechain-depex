from pydantic import BaseModel, Field, field_validator

from app.schemas.patterns import NEO4J_ID_PATTERN
from app.schemas.enums import Agregator, NodeType
from app.schemas.validators import validate_max_level


class ValidConfigRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_level: int = Field(...)
    node_type: NodeType
    agregator: Agregator
    config: dict[str, str]

    @field_validator("max_level")
    def validate_max_level(cls, value):
        return validate_max_level(value)
