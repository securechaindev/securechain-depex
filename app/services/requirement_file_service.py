from bson import ObjectId

from app.services.dbs.databases import requirement_file_collection


async def create_requirement_file(requirement_file_data: dict) -> dict:
    requirement_file = await requirement_file_collection.insert_one(requirement_file_data)
    new_requirement_file = await requirement_file_collection.find_one({'_id': requirement_file.inserted_id})
    return new_requirement_file

async def read_requirement_file_by_id(requirement_file_id: ObjectId, fields_to_remove: dict = {}) -> dict:
    graph = await requirement_file_collection.find_one({'_id': requirement_file_id}, fields_to_remove)
    return graph

async def update_requirement_file_package_edges(requirement_file_id: ObjectId, package_edge_id: ObjectId) -> None:
    await requirement_file_collection.find_one_and_update({'_id': requirement_file_id}, {'$push': {'package_edges': package_edge_id}})