from pydantic import BaseModel, Field


class VersionModel(BaseModel):
    release: str = Field(...)
    release_date: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "reseale": "urllib3",
            }
        }