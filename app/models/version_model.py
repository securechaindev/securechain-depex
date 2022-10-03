from pydantic import BaseModel, Field

from datetime import datetime

from app.models.package_edge_model import PackageEdgeModel
from app.models.cve_model import CveModel


class VersionModel(BaseModel):
    release: str = Field(...)
    mayor: int = Field(...)
    minor: int = Field(...)
    patch: int | None = Field(...)
    build_number: int = Field(...)
    release_date: datetime | None = Field(...)
    package_edges: list[PackageEdgeModel] | None = None
    cves: list[CveModel] | None = None
    package: dict | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'release': 'urllib3',
                'mayor': 1,
                'minor': 26,
                'patch': 5,
                'build_number': 0,
                'release_date': datetime.now(),
                'cves': [],
                'package': None
            }
        }