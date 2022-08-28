from pydantic import BaseSettings


class Settings(BaseSettings):

    DATABASE_URL: str | None = None
    GIT_GRAPHQL_API_KEY: str | None = None

    class Config:
        env_file = '.env'