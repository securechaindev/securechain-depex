from pydantic import BaseModel, Field

from app.models.requirement_file_model import RequirementFile


class GraphModel(BaseModel):
    owner: str = Field(..., min_length = 1, description = "The owner repository size must be greater than zero")
    name: str = Field(..., min_length = 1, description = "The name repository size must be greater than zero")
    add_extras: bool = Field(...)
    is_complete: bool = Field(...)
    requirement_files: list[RequirementFile] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'owner': 'psf',
                'name': 'requests',
                'add_extras': False,
                'is_complete': False
            }
        }