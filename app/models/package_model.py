from pydantic import BaseModel, Field


class PackageModel(BaseModel):
    name: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "name": "cryptography",
            }
        }