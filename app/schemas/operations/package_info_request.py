from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithMaxDepth
from app.schemas.enums import NodeType


class PackageInfoRequest(BaseSchemaWithMaxDepth):
    package_name: str = Field(...)
    max_depth: int = Field(...)
    node_type: NodeType = Field(...)
