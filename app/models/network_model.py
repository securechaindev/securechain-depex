# from bson import ObjectId

from pydantic import BaseModel, Field


class NetworkModel(BaseModel):
    owner: str = Field(..., min_length = 1, description = 'The owner repository size must be greater than zero')
    name: str = Field(..., min_length = 1, description = 'The name repository size must be greater than zero')
    add_extras: bool = Field(...)
    is_complete: bool = Field(...)
    # Buscar forma de poder tipar esto con ObjectId
    requirement_files: list | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'owner': 'GermanMT',
                'name': 'prueba',
                'add_extras': False,
                'is_complete': False,
                'requirement_files': []
            }
        }