import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from neo4j import AsyncGraphDatabase
from pymongo import AsyncMongoClient

from app.main import app
from app.settings import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
async def mongo_client() -> AsyncGenerator[AsyncMongoClient]:
    client = AsyncMongoClient(settings.VULN_DB_URI)
    yield client
    client.close()


@pytest.fixture
async def neo4j_driver() -> AsyncGenerator:
    driver = AsyncGraphDatabase.driver(
        settings.GRAPH_DB_URI,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD)
    )
    yield driver
    await driver.close()


@pytest.fixture
def sample_repository_data() -> dict:
    return {
        "owner": "test-owner",
        "name": "test-repo",
        "moment": "2025-10-27T00:00:00",
        "is_complete": True
    }


@pytest.fixture
def sample_package_data() -> dict:
    return {
        "name": "fastapi",
        "manager": "PyPI",
        "constraints": ">= 0.100.0, < 1.0.0"
    }


@pytest.fixture
def sample_requirement_file() -> dict:
    return {
        "requirements.txt": {
            "manager": "PyPI",
            "packages": {
                "fastapi": ">= 0.100.0",
                "uvicorn": "== 0.35.0",
                "pydantic": ">= 2.0.0, < 3.0.0"
            }
        }
    }
