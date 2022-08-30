from bson import ObjectId

from app.services.dbs.databases import package_collection


async def add_package(package_data: dict) -> dict:
    package = await package_collection.insert_one(package_data)
    new_package = await package_collection.find_one({'_id': package.inserted_id})
    return new_package

async def get_package_by_name_in_graph(package_name: str, graph_id: ObjectId) -> dict:
    package = await package_collection.find_one({'$and': [{'name': package_name}, {'graph': graph_id}]})
    return package

async def get_package_by_name(package_name: str) -> dict:
    package = await package_collection.find_one({'name': package_name})
    return package

async def update_package_versions(package_id: ObjectId, versions: list) -> dict:
    updated_package = await package_collection.find_one_and_update({'_id': package_id}, {'$set': {'versions': versions}})
    return updated_package