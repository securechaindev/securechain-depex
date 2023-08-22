from typing import Any
from functools import lru_cache
from neo4j import AsyncGraphDatabase, AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from app.config import settings


@lru_cache
def get_graph_db_session(package_manager: str) -> AsyncSession | tuple[AsyncSession]:
    pip_session = AsyncGraphDatabase.driver(uri=settings.GRAPH_DB_URI_PIP, auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_PIP)).session()
    npm_session = AsyncGraphDatabase.driver(uri=settings.GRAPH_DB_URI_NPM, auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_NPM)).session()
    mvn_session = AsyncGraphDatabase.driver(uri=settings.GRAPH_DB_URI_MVN, auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD_MVN)).session()
    match package_manager:
        case 'PIP':
            return pip_session
        case 'NPM':
            return npm_session
        case 'MVN':
            return mvn_session
        case 'ALL':
            return pip_session, npm_session, mvn_session
        case _:
            return pip_session


@lru_cache
def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    client = AsyncIOMotorClient(settings.VULN_DB_URI)
    match collection_name:
        case 'env_variables':
            return client.depex.get_collection('env_variables')
        case 'nvd':
            return client.cves.get_collection('nvd')
        case 'exploit_db':
            return client.exploits.get_collection('exploit_db')
        case _:
            return client.exploits.get_collection('exploits')