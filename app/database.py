from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import settings
from app.constants import DatabaseConfig
from app.logger import logger


class DatabaseManager:
    instance: "DatabaseManager | None" = None
    mongo_client: AsyncIOMotorClient | None = None
    neo4j_driver: AsyncDriver | None = None
    securechain_db: AsyncIOMotorDatabase | None = None
    vulnerabilities_db: AsyncIOMotorDatabase | None = None

    def __new__(cls) -> "DatabaseManager":
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    async def initialize(self) -> None:
        if self.mongo_client is None:
            logger.info("Initializing MongoDB connection pool...")
            self.mongo_client = AsyncIOMotorClient(
                settings.VULN_DB_URI,
                minPoolSize=DatabaseConfig.MIN_POOL_SIZE,
                maxPoolSize=DatabaseConfig.MAX_POOL_SIZE,
                maxIdleTimeMS=DatabaseConfig.MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=DatabaseConfig.DEFAULT_QUERY_TIMEOUT_MS,
            )
            self.securechain_db = self.mongo_client.get_database("securechain")
            self.vulnerabilities_db = self.mongo_client.get_database("vulnerabilities")
            logger.info("MongoDB connection pool initialized")

        if self.neo4j_driver is None:
            logger.info("Initializing Neo4j driver...")
            self.neo4j_driver = AsyncGraphDatabase.driver(
                uri=settings.GRAPH_DB_URI,
                auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD),
                max_connection_pool_size=DatabaseConfig.MAX_POOL_SIZE,
            )
            logger.info("Neo4j driver initialized")

    async def close(self) -> None:
        if self.mongo_client:
            logger.info("Closing MongoDB connection...")
            self.mongo_client.close()
            self.mongo_client = None
            self.securechain_db = None
            self.vulnerabilities_db = None
            logger.info("MongoDB connection closed")

        if self.neo4j_driver:
            logger.info("Closing Neo4j driver...")
            await self.neo4j_driver.close()
            self.neo4j_driver = None
            logger.info("Neo4j driver closed")

    def get_user_collection(self) -> AsyncIOMotorCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(DatabaseConfig.USERS_COLLECTION)

    def get_smt_text_collection(self) -> AsyncIOMotorCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(DatabaseConfig.SMT_TEXT_COLLECTION)

    def get_operation_result_collection(self) -> AsyncIOMotorCollection:
        if self.securechain_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.securechain_db.get_collection(DatabaseConfig.OPERATION_RESULT_COLLECTION)

    def get_vulnerabilities_collection(self) -> AsyncIOMotorCollection:
        if self.vulnerabilities_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.vulnerabilities_db.get_collection("vulnerabilities")

    def get_cwes_collection(self) -> AsyncIOMotorCollection:
        if self.vulnerabilities_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.vulnerabilities_db.get_collection("cwes")

    def get_exploits_collection(self) -> AsyncIOMotorCollection:
        if self.vulnerabilities_db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.vulnerabilities_db.get_collection("exploits")

    def get_neo4j_driver(self) -> AsyncDriver:
        if self.neo4j_driver is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.neo4j_driver
