from pydantic import BaseModel, Field


class PackageModel(BaseModel):
    # level: int = Field(...)
    name: str = Field(...)
    # parent_rel: PackageEdgeModel | None  = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                # "level": "2",
                "name": "cryptography",
            }
        }