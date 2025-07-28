from functools import lru_cache

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import settings


@lru_cache
def get_graph_db_driver() -> AsyncDriver:
    return AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD),
    )


@lru_cache
def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.VULN_DB_URI)
    securechain_db: AsyncIOMotorDatabase = client.get_database("securechain")
    vulnerabilities_db: AsyncIOMotorDatabase = client.get_database("vulnerabilities")
    match collection_name:
        case "smt_text":
            return securechain_db.get_collection(collection_name)
        case "operation_result":
            return securechain_db.get_collection(collection_name)
        case "vulnerabilities":
            return vulnerabilities_db.get_collection(collection_name)
