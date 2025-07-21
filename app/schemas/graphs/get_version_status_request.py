from pydantic import BaseModel, Field

from app.schemas.enums import NodeType


class GetVersionStatusRequest(BaseModel):
    name: str  = Field(...)
    package_name: str = Field(...)
    node_type: NodeType = Field(...)

