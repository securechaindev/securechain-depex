from bson.objectid import ObjectId

from app.services.db.database import graph_collection


async def add_graph(graph_data: dict) -> dict:
    graph = await graph_collection.insert_one(graph_data)
    new_graph = await graph_collection.find_one({"_id": graph.inserted_id})
    return new_graph