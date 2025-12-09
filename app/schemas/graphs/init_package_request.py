from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithPackageName
from app.schemas.enums import NodeType


class InitPackageRequest(BaseSchemaWithPackageName):
    node_type: NodeType = Field(...)
    package_name: str = Field(...)
    vendor: str = Field(default="n/a")
    repository_url: str = Field(default="n/a")
    constraints: str | None = Field(default=None)
    parent_id: str | None = Field(default=None)
    parent_version: str | None = Field(default=None)
    refresh: bool = Field(default=False)
