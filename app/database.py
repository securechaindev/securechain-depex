from neo4j import AsyncDriver, AsyncGraphDatabase
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.logger import logger
from app.settings import settings


class DatabaseManager:
    instance: DatabaseManager | None = None
    mongo_client: AsyncMongoClient | None = None
    neo4j_driver: AsyncDriver | None = None
    securechain_db: AsyncDatabase | None = None
    vulnerabilities_db: AsyncDatabase | None = None

    def __new__(cls) -> DatabaseManager:
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    async def initialize(self) -> None:
        if self.mongo_client is None:
            logger.info("Initializing MongoDB connection pool...")
            self.mongo_client = AsyncMongoClient(
                settings.VULN_DB_URI,
                minPoolSize=settings.DB_MIN_POOL_SIZE,
                maxPoolSize=settings.DB_MAX_POOL_SIZE,
                maxIdleTimeMS=settings.DB_MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=settings.DB_DEFAULT_QUERY_TIMEOUT_MS,
            )
            self.securechain_db = self.mongo_client.get_database("securechain")
            self.vulnerabilities_db = self.mongo_client.get_database("vulnerabilities")
            logger.info("MongoDB connection pool initialized")

        if self.neo4j_driver is None:
            logger.info("Initializing Neo4j driver...")
            self.neo4j_driver = AsyncGraphDatabase.driver(
                uri=settings.GRAPH_DB_URI,
                auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD),
                max_connection_pool_size=settings.DB_MAX_POOL_SIZE,
            )
            logger.info("Neo4j driver initialized")

    async def close(self) -> None:
        if self.mongo_client:
            logger.info("Closing MongoDB connection...")
            await self.mongo_client.close()
            self.mongo_client = None
            self.securechain_db = None
            self.vulnerabilities_db = None
            logger.info("MongoDB connection closed")

        if self.neo4j_driver:
            logger.info("Closing Neo4j driver...")
            await self.neo4j_driver.close()
            self.neo4j_driver = None
            logger.info("Neo4j driver closed")

    def get_smts_collection(self) -> AsyncCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(settings.DB_SMTS_COLLECTION)

    def get_operation_results_collection(self) -> AsyncCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(settings.DB_OPERATION_RESULT_COLLECTION)

    def get_api_keys_collection(self) -> AsyncCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(settings.DB_API_KEY_COLLECTION)

    def get_neo4j_driver(self) -> AsyncDriver:
        if self.neo4j_driver is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.neo4j_driver
