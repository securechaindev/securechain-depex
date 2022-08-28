from bson import ObjectId

from app.services.db.database import requirement_file_collection


async def add_requirement_file(requirement_file_data: dict) -> dict:
    requirement_file = await requirement_file_collection.insert_one(requirement_file_data)
    new_requirement_file = await requirement_file_collection.find_one({'_id': requirement_file.inserted_id})
    return new_requirement_file

async def update_requirement_file(requirement_file_id: ObjectId, package_edges: list) -> dict:
    updated_requirement_file = await requirement_file_collection.find_one_and_update({'_id': requirement_file_id}, {'$set': {'package_edges': package_edges}})
    return updated_requirement_file