import motor.motor_asyncio


client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")

db = client.advisory

graph_collection = db.get_collection("graphs")
package_collection = db.get_collection("packages")
version_collection = db.get_collection("versions")