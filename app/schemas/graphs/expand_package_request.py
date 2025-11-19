from pydantic import BaseModel, Field

from app.schemas.enums import NodeType


class ExpandPackageRequest(BaseModel):
    node_type: NodeType = Field(...)
    package_purl: str = Field(
        ...,
        pattern=r"^pkg:[a-z]+(/[^/]+)+$",
        description="Package URL following the purl specification (e.g., pkg:pypi/django)"
    )
    constraints: str | None = Field(..., description="Version constraints for the package (e.g., '>=2.0.0,<3.0.0')")
