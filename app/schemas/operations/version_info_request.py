from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithMaxDepthMinusOne
from app.schemas.enums import NodeType


class VersionInfoRequest(BaseSchemaWithMaxDepthMinusOne):
    package_name: str = Field(...)
    version_name: str = Field(...)
    max_depth: int = Field(...)
    node_type: NodeType = Field(...)
