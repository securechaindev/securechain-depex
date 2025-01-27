from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GRAPH_DB_URI: str = ""
    GRAPH_DB_USER: str = ""
    GRAPH_DB_PASSWORD: str = ""
    VULN_DB_URI: str = ""
    VULN_DB_USER: str = ""
    VULN_DB_PASSWORD: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0
    JWT_SECRET_KEY: str = ""
    GITHUB_GRAPHQL_API_KEY: str = ""
    NVD_API_KEY: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
