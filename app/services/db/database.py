import motor.motor_asyncio

from functools import lru_cache

from app.config import Settings


@lru_cache()
def get_settings():
    return Settings()


settings: Settings = get_settings()

client = motor.motor_asyncio.AsyncIOMotorClient(settings.DATABASE_URL)

db = client.depex

graph_collection = db.get_collection("graphs")
package_collection = db.get_collection("packages")
package_edge_collection = db.get_collection("package_edges")
version_collection = db.get_collection("versions")