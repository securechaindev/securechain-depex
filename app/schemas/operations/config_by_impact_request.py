from pydantic import BaseModel, Field, validator

from app.models.patterns import NEO4J_ID_PATTERN
from app.models.utils import Agregator, NodeType
from app.models.validators import validate_max_level


class ConfigByImpactRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_level: int = Field(...)
    impact: float = Field(
        ge=0,
        le=10
    )
    node_type: NodeType
    agregator: Agregator

    @validator("max_level")
    def validate_max_level(cls, value):
        return validate_max_level(value)
