from bson import ObjectId

from pydantic import BaseModel, Field


class PackageEdgeModel(BaseModel):
    constraints: list[list[str]] | str = Field(...)
    versions: ObjectId | None = None
    package: ObjectId | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'constraints': [['<=', '0.7.0'], ['==', '1.2.1'], ['>', '2.3']],
                'versions': [],
                'package': None
            }
        }