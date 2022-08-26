from pydantic import BaseModel, Field

# from app.models.package_model import PackageModel
# from app.models.version_model import VersionModel


class PackageEdgeModel(BaseModel):
    constraints: list[list[str]] | str = Field(...)
    # PackageModel | None
    package = None
    # list[VersionModel] | None
    versions = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'constraints': [['<=', '0.7.0'], ['==', '1.2.1'], ['>', '2.3']],
            }
        }