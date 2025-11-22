from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    GRAPH_DB_URI: str = ""
    GRAPH_DB_USER: str = ""
    GRAPH_DB_PASSWORD: str = ""
    VULN_DB_URI: str = ""
    VULN_DB_USER: str = ""
    VULN_DB_PASSWORD: str = ""
    DOCS_URL: str | None = None
    SERVICES_ALLOWED_ORIGINS: list[str] = []
    ALGORITHM: str = ""
    JWT_ACCESS_SECRET_KEY: str = ""
    GITHUB_GRAPHQL_API_KEY: str = ""

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_STREAM: str = "package-extraction"
    REDIS_GROUP: str = "extractors"
    REDIS_CONSUMER: str = "package-consumer"

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
