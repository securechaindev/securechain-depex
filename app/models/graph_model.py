from pydantic import BaseModel, Field


class GraphModel(BaseModel):
    owner: str = Field(...)
    name: str = Field(...)
    manager: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "owner": "urllib3",
                "name": "urllib3",
                "manager": "PIP"
            }
        }