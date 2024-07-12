from enum import Enum

from pydantic import BaseModel, Field, validator

from .validators import validate_max_level


class User(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AccountExistsRequest(BaseModel):
    email: str


class VerifyAccessTokenRequest(BaseModel):
    access_token: str | None


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str


class InitGraphRequest(BaseModel):
    owner: str
    name: str
    user_id: str


class PackageManager(str, Enum):
    pip = "PIP"
    npm = "NPM"
    mvn = "MVN"


class Agregator(str, Enum):
    mean = "mean"
    weighted_mean = "weighted_mean"


class FileInfoRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_level: int = Field(...)
    package_manager: PackageManager

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class ValidFileRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_level: int = Field(...)
    package_manager: PackageManager

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class MinMaxImpactRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    limit: int = Field(
        ge=1
    )
    max_level: int = Field(...)
    package_manager: PackageManager
    agregator: Agregator

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class FilterConfigsRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_threshold: float = Field(
        ge=0,
        le=10
    )
    min_threshold: float = Field(
        ge=0,
        le=10
    )
    limit: int = Field(
        ge=1
    )
    max_level: int = Field(...)
    package_manager: PackageManager
    agregator: Agregator

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class ValidConfigRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_level: int = Field(...)
    package_manager: PackageManager
    agregator: Agregator
    config: dict[str, str]

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class CompleteConfigRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_level: int = Field(...)
    package_manager: PackageManager
    agregator: Agregator
    config: dict[str, str]

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)


class ConfigByImpactRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern="^4:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:[0-9]+$"
    )
    max_level: int = Field(...)
    impact: float = Field(
        ge=0,
        le=10
    )
    package_manager: PackageManager
    agregator: Agregator

    @validator('max_level')
    def validate_max_level(cls, value):
        return validate_max_level(value)
