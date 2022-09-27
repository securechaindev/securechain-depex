from pydantic import BaseModel, Field


class WeaknessModel(BaseModel):
    source: str = Field(...)
    value: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'source': 'nvd@nist.gov',
                'value': 'CWE-290'
            }
        }