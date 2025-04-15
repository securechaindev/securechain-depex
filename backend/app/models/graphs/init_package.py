from pydantic import BaseModel, Field

from app.models.utils import NodeType


class InitPackageRequest(BaseModel):
    name: str  = Field(...)
    artifact_id: str | None = Field(...)
    node_type: NodeType = Field(...)
