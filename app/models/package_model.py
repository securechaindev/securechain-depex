from pydantic import BaseModel, Field

from app.models.graph_model import GraphModel
from app.models.version_model import VersionModel


class PackageModel(BaseModel):
    name: str = Field(...)
    graph: GraphModel | None = None
    versions: list[VersionModel] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "name": "urllib3",
            }
        }