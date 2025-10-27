from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithPackageName
from app.schemas.enums import NodeType


class GetPackageStatusRequest(BaseSchemaWithPackageName):
    node_type: NodeType = Field(...)
    package_name: str = Field(...)
