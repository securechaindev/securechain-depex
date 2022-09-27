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
    base_core: str = Field(...)
    base_severity: str = Field(...)
    exploitability_score: str = Field(...)
    impact_score: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'vectorString': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N',
                'attackVector': 'NETWORK',
                'attackComplexity': 'LOW',
                'privilegesRequired': 'NONE',
                'userInteraction': 'NONE',
                'scope': 'UNCHANGED',
                'confidentialityImpact': 'NONE',
                'integrityImpact': 'LOW',
                'availabilityImpact': 'NONE',
                'baseScore': 5.3,
                'baseSeverity': 'MEDIUM',
                'exploitabilityScore': 3.9,
                'impactScore': 1.4
            }
        }