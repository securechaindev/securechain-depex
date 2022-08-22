from app.services.db.database import package_edge_collection


async def add_package_edge(package_edge_data: dict) -> dict:
    package_edge = await package_edge_collection.insert_one(package_edge_data)
    new_package_edge = await package_edge_collection.find_one({"_id": package_edge.inserted_id})
    return new_package_edge