from pydantic import BaseModel

from app.models.package_model import PackageModel


class PackageEdgeModel(BaseModel):
    constraints: list[str] | None = None
    package: PackageModel | None = None
    schema_extra = {
            "example": {
                "constraints": ["<=0.7.0", "==1.2.1", ">2.3"],
            }
        }

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True