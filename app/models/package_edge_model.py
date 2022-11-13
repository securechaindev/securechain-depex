from pydantic import BaseModel, Field

from app.models.package_model import VersionModel


class PackageEdgeModel(BaseModel):
    package_name: str = Field(...)
    constraints: list[list[str]] | str = Field(...)
    versions: list[VersionModel] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'package_name': 'urllib3',
                'constraints': [['<=', '0.7.0'], ['==', '1.2.1'], ['>', '2.3']],
                'versions': []
            }
        }