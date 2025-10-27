from pydantic import Field

from app.schemas.base_schema import BaseSchemaWithPackageName
from app.schemas.enums import NodeType


class GetVersionStatusRequest(BaseSchemaWithPackageName):
    node_type: NodeType = Field(...)
    package_name: str = Field(...)
    version_name: str = Field(...)
