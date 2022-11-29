from typing import Any

from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field

# Poner todos los modelos en un mismo archivo .py para hacerlo más pytonic
# from app.models.package_model import PackageModel


class VersionModel(BaseModel):
    release: str = Field(...)
    mayor: int = Field(...)
    minor: int = Field(...)
    patch: int | None = Field(...)
    build_number: int | None = Field(...)
    release_date: datetime | None = Field(...)
    cves: list[ObjectId] | None = None
    package: dict[str, Any] | None = None

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