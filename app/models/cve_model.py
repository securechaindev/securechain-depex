from datetime import datetime

from bson import ObjectId
from dateutil.parser import parse
from pydantic import BaseModel, Field


class CveModel(BaseModel):
    cve_id: str = Field(...)
    source_identifier: str = Field(...)
    published: datetime = Field(...)
    last_modified: datetime = Field(...)
    vuln_status: str = Field(...)
    description: str = Field(...)
    configurations: list[ObjectId] | None = None
    weaknesses: list[ObjectId] | None = None
    metrics: list[ObjectId] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'cve_id': 'CVE-2019-20203',
                'source_identifier': 'security@netgear.com',
                'published': parse('2020-01-02T14:16:35.987'),
                'last_modified': parse('2020-08-24T17:37:01.140'),
                'vuln_status': 'Analyzed',
                'description': 'The Authorized Addresses feature in the Postie plugin 1.9.40 for WordPress allows ...',
                'configurations': [],
                'weaknesses': [],
                'metrics': []
            }
        }