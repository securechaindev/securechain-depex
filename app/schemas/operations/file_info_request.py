from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.enums import NodeType
from app.schemas.patterns import NEO4J_ID_PATTERN
from app.schemas.validators import validate_max_depth


class FileInfoRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_depth: int = Field(...)
    node_type: NodeType = Field(...)

    @field_validator("max_depth")
    def validate_max_depth(cls, value):
        return validate_max_depth(value)

    @model_validator(mode='before')
    def set_max_depth_to_square(cls, values):
        if values.get('max_depth') != -1:
            values['max_depth'] = (values.get('max_depth', 1) * 2) - 1
        return values
