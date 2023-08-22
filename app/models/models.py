from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field


class VersionModel(BaseModel):
    release: str
    release_date: datetime | None
    count: int
    cves: list[dict[Any, Any]] | None
    mean: int
    weighted_mean: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            'example': {
                'release': '1.26.5',
                'release_date': datetime.now(),
                'count': 23,
                'cves': [],
                'mean': 0, 
                'weighted_mean': 0
            }
        }


class PackageModel(BaseModel):
    name: str
    moment: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            'example': {
                'name': 'urllib3',
                'moment': datetime.now()
            }
        }


class RequirementFile(BaseModel):
    name: str
    manager: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
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
    moment: datetime
    add_extras: bool
    is_complete: bool

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            'example': {
                'owner': 'depexorg',
                'name': 'pip_test',
                'moment': datetime.now(),
                'add_extras': False,
                'is_complete': False
            }
        }