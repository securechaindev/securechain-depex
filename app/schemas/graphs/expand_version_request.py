from pydantic import BaseModel, Field


class ExpandVersionRequest(BaseModel):
    version_purl: str = Field(
        ...,
        pattern=r"^pkg:[a-z]+(/[^/]+)+@[^@]+$",
        description="Version Package URL following the purl specification (e.g., pkg:pypi/django@4.2.0)"
    )
