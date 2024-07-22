from functools import lru_cache

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import settings


@lru_cache
def get_graph_db_driver(package_manager: str) -> AsyncDriver | tuple[AsyncDriver]:
    pip_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_PIP,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_PIP),
    )
    npm_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_NPM,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_NPM),
    )
    mvn_driver: AsyncDriver = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_MVN,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_MVN),
    )
    match package_manager:
        case "PIP":
            return pip_driver
        case "NPM":
            return npm_driver
        case "MVN":
            return mvn_driver
        case "ALL":
            return pip_driver, npm_driver, mvn_driver


@lru_cache
def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.VULN_DB_URI)
    depex_db: AsyncIOMotorDatabase = client.depex
    nvd_db: AsyncIOMotorDatabase = client.nvd
    match collection_name:
        case "env_variables":
            return depex_db.get_collection(collection_name)
        case "users":
            return depex_db.get_collection(collection_name)
        case "jwt_tokens":
            return depex_db.get_collection(collection_name)
        case "smt_text":
            return depex_db.get_collection(collection_name)
        case "cves":
            return nvd_db.get_collection(collection_name)
        case "cpe_matchs":
            return nvd_db.get_collection(collection_name)
        case "cpes":
            return nvd_db.get_collection(collection_name)
        case "cpe_products":
            return nvd_db.get_collection(collection_name)
