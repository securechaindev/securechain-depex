from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from neo4j import AsyncGraphDatabase, AsyncSession

from app.config import settings


@lru_cache
def get_graph_db_session(package_manager: str) -> AsyncSession | tuple[AsyncSession]:
    pip_session: AsyncSession = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_PIP,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_PIP),
    ).session()
    npm_session: AsyncSession = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_NPM,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_NPM),
    ).session()
    mvn_session: AsyncSession = AsyncGraphDatabase.driver(
        uri=settings.GRAPH_DB_URI_MVN,
        auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_MVN),
    ).session()
    match package_manager:
        case "PIP":
            return pip_session
        case "NPM":
            return npm_session
        case "MVN":
            return mvn_session
        case "ALL":
            return pip_session, npm_session, mvn_session


@lru_cache
def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.VULN_DB_URI)
    match collection_name:
        case "env_variables":
            return client.depex.get_collection(collection_name)
        case "smt_text":
            return client.depex.get_collection(collection_name)
        case "cves":
            return client.nvd.get_collection(collection_name)
        case "cpe_matchs":
            return client.nvd.get_collection(collection_name)
        case "cpes":
            return client.nvd.get_collection(collection_name)
        case "cpe_products":
            return client.nvd.get_collection(collection_name)
        case "exploits":
            return client.exploit_db.get_collection(collection_name)
