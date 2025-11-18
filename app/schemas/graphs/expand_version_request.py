from pydantic import BaseModel, Field


class ExpandVersionRequest(BaseModel):
    version_purl: str = Field(...)
