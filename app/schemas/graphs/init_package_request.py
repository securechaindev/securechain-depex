from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import NodeType


class InitPackageRequest(BaseModel):
    node_type: NodeType = Field(...)
    package_name: str = Field(...)
    vendor: str = Field(default="n/a")
    repository_url: str | None = Field(default=None)
    constraints: str | None = Field(default=None)
    parent_id: str | None = Field(default=None)
    parent_version: str | None = Field(default=None)
    refresh: bool = Field(default=False)

    @model_validator(mode='before')
    def set_package_name_to_lowercase(cls, values):
        values['package_name'] = values.get('package_name', '').lower()
        return values
