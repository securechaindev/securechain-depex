from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database connections (required)
    GRAPH_DB_URI: str = Field(..., alias="GRAPH_DB_URI")
    GRAPH_DB_USER: str = Field(..., alias="GRAPH_DB_USER")
    GRAPH_DB_PASSWORD: str = Field(..., alias="GRAPH_DB_PASSWORD")
    VULN_DB_URI: str = Field(..., alias="VULN_DB_URI")

    # GitHub API Key (required)
    GITHUB_GRAPHQL_API_KEY: str = Field(..., alias="GITHUB_GRAPHQL_API_KEY")

    # JWT secrets (required)
    JWT_ACCESS_SECRET_KEY: str = Field(..., alias="JWT_ACCESS_SECRET_KEY")

    # Application settings (safe defaults)
    DOCS_URL: str | None = Field(None, alias="DOCS_URL")
    SERVICES_ALLOWED_ORIGINS: list[str] = Field(["*"], alias="SERVICES_ALLOWED_ORIGINS")
    ALGORITHM: str = Field("HS256", alias="ALGORITHM")

    # Redis Configuration
    REDIS_HOST: str = Field("localhost", alias="REDIS_HOST")
    REDIS_PORT: int = Field(6379, alias="REDIS_PORT")
    REDIS_DB: int = Field(0, alias="REDIS_DB")
    REDIS_STREAM: str = Field("package-extraction", alias="REDIS_STREAM")
    REDIS_GROUP: str = Field("extractors", alias="REDIS_GROUP")
    REDIS_CONSUMER: str = Field("package-consumer", alias="REDIS_CONSUMER")

    # Database Configuration
    DB_MIN_POOL_SIZE: int = 10
    DB_MAX_POOL_SIZE: int = 100
    DB_MAX_IDLE_TIME_MS: int = 60000
    DB_DEFAULT_QUERY_TIMEOUT_MS: int = 30000
    DB_SMTS_COLLECTION: str = "smts"
    DB_OPERATION_RESULT_COLLECTION: str = "operation_results"
    DB_API_KEY_COLLECTION: str = "api_keys"

    # SMT Solver Configuration
    SMT_SOLVER_TIMEOUT_MS: int = 3000

    # Python Version Configuration
    MIN_PYTHON_VERSION_MAJOR: int = 3
    MIN_PYTHON_VERSION_MINOR: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
