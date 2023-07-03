from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field


class VersionModel(BaseModel):
    release: str
    mayor: int
    minor: int
    patch: int | None
    build_number: int | None
    release_date: datetime | None
    package_eges: list[dict[Any, Any]] | None
    cves: list[dict[Any, Any]] | None
    package: str
    count: int

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'release': '1.26.5',
                'release_date': datetime.now(),
                'count': 23,
                'cves': [],
            }
        }


class PackageModel(BaseModel):
    name: str
    moment: datetime
    versions: list[VersionModel] | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'name': 'urllib3',
                'moment': datetime.now()
            }
        }


class RequirementFile(BaseModel):
    name: str
    manager: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'name': 'requirements.txt',
                'manager': 'PIP'
            }
        }


class RepositoryModel(BaseModel):
    owner: str = Field(
        ...,
        min_length=1,
        description='The owner repository size must be greater than zero'
    )
    name: str = Field(
        ...,
        min_length=1,
        description='The name repository size must be greater than zero'
    )
    add_extras: bool
    is_complete: bool
    requirement_files: list[RequirementFile] | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'owner': 'GermanMT',
                'name': 'prueba_pypi',
                'add_extras': False,
                'is_complete': False
            }
        }