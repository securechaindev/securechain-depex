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
                'release': 'urllib3',
                'mayor': 1,
                'minor': 26,
                'patch': 5,
                'build_number': 0,
                'release_date': datetime.now(),
                'package_edges': [],
                'cves': [],
                'package': 'request',
                'count': 23
            }
        }


class PackageEdgeModel(BaseModel):
    package_name: str
    constraints: list[list[str]] | str
    versions: list[VersionModel] | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'package_name': 'urllib3',
                'constraints': [['<=', '0.7.0'], ['==', '1.2.1'], ['>', '2.3']],
                'versions': []
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
                'moment': datetime.now(),
                'versions': []
            }
        }


class RequirementFile(BaseModel):
    name: str
    manager: str
    package_edges: list[PackageEdgeModel]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            'example': {
                'name': 'requirements.txt',
                'manager': 'PIP',
                'package_edges': []
            }
        }


class GraphModel(BaseModel):
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
                'name': 'prueba',
                'add_extras': False,
                'is_complete': False,
                'requirement_files': []
            }
        }