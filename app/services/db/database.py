import motor.motor_asyncio

from app.config import Settings


client = motor.motor_asyncio.AsyncIOMotorClient(Settings().DATABASE_URL)

db = client.advisory

graph_collection = db.get_collection("graphs")
package_collection = db.get_collection("packages")
version_collection = db.get_collection("versions")