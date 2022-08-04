from pydantic import BaseModel, Field

from app.models.package_model import PackageModel


class GraphModel(BaseModel):
    owner: str = Field(...)
    name: str = Field(...)
    manager: str = Field(...)
    # root: PackageModel | None = None
    packages: list[PackageModel] | None = None
    # relationships: list['RelationshipModel'] | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "owner": "urllib3",
                "name": "urllib3",
                "manager": "PIP"
            }
        }