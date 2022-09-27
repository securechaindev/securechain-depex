from pydantic import BaseModel, Field

from datetime import datetime

from app.models.package_edge_model import PackageEdgeModel
from app.models.cve_model import CveModel


class VersionModel(BaseModel):
    release: str = Field(...)
    release_date: datetime = Field(...)
    package_edges: list[PackageEdgeModel] | None = None
    cves: list[CveModel] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'release': 'urllib3',
                'release_date': datetime.now(),
                'cves': []
            }
        }