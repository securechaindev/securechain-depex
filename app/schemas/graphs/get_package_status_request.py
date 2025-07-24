from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import NodeType


class GetPackageStatusRequest(BaseModel):
    node_type: NodeType = Field(...)
    package_name: str  = Field(...)

    @model_validator(mode='before')
    def set_package_name_to_lowercase(cls, values):
        values['package_name'] = values.get('package_name', '').lower()
        return values
