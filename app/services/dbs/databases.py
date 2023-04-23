from neo4j import AsyncGraphDatabase

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

DRIVER = AsyncGraphDatabase.driver(
    uri=settings.GRAPH_DB_URI,
    auth=(settings.GRAPH_DB_USER, settings.GRAPH_DB_PASSWORD)
)

session = DRIVER.session()

client = AsyncIOMotorClient(settings.VULN_DB_URI)

depex_db = client.depex
env_variable_collection = depex_db.get_collection('env_variables')

nvd_db = client.nvd
cve_collection = nvd_db.get_collection('cves')