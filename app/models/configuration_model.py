from pydantic import BaseModel, Field


class ConfigurationModel(BaseModel):
    vulnerable: bool = Field(...)
    cpe_match_criterias: list[str] = Field(...)
    version_start_including: str | None = Field(...)
    version_end_including: str | None = Field(...)
    version_start_excluding: str | None = Field(...)
    version_end_excluding: str | None = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'vulnerable': True,
                'cpe_match_criterias': [
                    'cpe:2.3:a:python:requests:*:*:*:*:*:*:*:*'
                ],
                'version_start_excluding': '1.1.0',
                'version_end_including': '2.2.1'
            }
        }