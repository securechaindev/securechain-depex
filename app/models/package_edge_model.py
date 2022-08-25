from pydantic import BaseModel

# from app.models.package_model import PackageModel
# from app.models.version_model import VersionModel


class PackageEdgeModel(BaseModel):
    constraints: list[str] | None = None
    # PackageModel | None
    package = None
    # list[VersionModel] | None
    versions = None
    schema_extra = {
            'example': {
                'constraints': ['<=0.7.0', '==1.2.1', '>2.3'],
            }
        }

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True