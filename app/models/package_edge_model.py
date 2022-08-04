from pydantic import BaseModel, Field

from app.models.version_model import VersionModel


class PackageEdgeModel(BaseModel):
    parent: 'VersionModel' = Field(...)
    # child: 'PackageModel' | None = None
    constraints: list[str] | None = None
    schema_extra = {
            "example": {
                "constraints": "[<=0.7.0, ==1.2.1, >2.3]",
            }
        }

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True