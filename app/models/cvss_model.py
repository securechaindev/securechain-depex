from pydantic import BaseModel, Field


class CvssModel(BaseModel):
    vector_string: str = Field(...)
    attack_vector: str = Field(...)
    attack_complexity: str = Field(...)
    privileges_required: str = Field(...)
    user_interaction: str = Field(...)
    scope: str = Field(...)
    confidentiality_impact: str = Field(...)
    integrity_impact: str = Field(...)
    availability_impact: str = Field(...)
    base_score: str = Field(...)
    base_severity: str = Field(...)
    exploitability_score: str = Field(...)
    impact_score: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'vector_string': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N',
                'attack_vector': 'NETWORK',
                'attack_complexity': 'LOW',
                'privileges_required': 'NONE',
                'user_interaction': 'NONE',
                'scope': 'UNCHANGED',
                'confidentiality_impact': 'NONE',
                'integrity_impact': 'LOW',
                'availability_impact': 'NONE',
                'base_score': 5.3,
                'base_severity': 'MEDIUM',
                'exploitability_score': 3.9,
                'impact_score': 1.4
            }
        }