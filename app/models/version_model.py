from pydantic import BaseModel, Field

from app.models.package_edge_model import PackageEdgeModel


class VersionModel(BaseModel):
    release: str = Field(...)
    release_date: str = Field(...)
    package_edges: list[PackageEdgeModel] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "release": "urllib3",
                "release_date": "2015-05-21T09:30:06"
            }
        }