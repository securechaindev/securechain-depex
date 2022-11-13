from pydantic import BaseModel, Field


class RequirementFile(BaseModel):
    name: str = Field(...)
    manager: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'name': 'requirements.txt',
                'manager': 'PIP'
            }
        }