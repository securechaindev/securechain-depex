from pydantic import BaseModel, Field

from app.models.package_edge_model import PackageEdgeModel


class RequirementFile(BaseModel):
    name: str = Field(...)
    package_edges: list[PackageEdgeModel] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'name': 'requirements.txt'
            }
        }