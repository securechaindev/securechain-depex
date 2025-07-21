from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import NodeType


class InitPackageRequest(BaseModel):
    name: str  = Field(...)
    node_type: NodeType = Field(...)

    @model_validator(mode='before')
    def set_name_to_lowercase(cls, values):
        values['name'] = values.get('name', '').lower()
        return values
