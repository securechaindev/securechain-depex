from pydantic import BaseModel, Field

from app.schemas.utils import NodeType


class InitPackageRequest(BaseModel):
    name: str  = Field(...)
    node_type: NodeType = Field(...)
