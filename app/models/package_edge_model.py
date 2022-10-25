from pydantic import BaseModel, Field

from app.models.requirement_file_model import RequirementFile
from app.models.package_model import PackageModel, VersionModel


class PackageEdgeModel(BaseModel):
    constraints: list[list[str]] | str = Field(...)
    versions: list[VersionModel] | None = None
    parent: VersionModel | RequirementFile | None = None
    child: PackageModel | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'constraints': [['<=', '0.7.0'], ['==', '1.2.1'], ['>', '2.3']],
                'versions': [],
                'parent': None,
                'child': None
            }
        }