from datetime import datetime

from bson import ObjectId

from app.services.dbs.databases import package_collection


async def create_package(package_data: dict) -> dict:
    package = await package_collection.insert_one(package_data)
    new_package = await package_collection.find_one({'_id': package.inserted_id})
    return new_package

async def read_package_by_name(package_name: str) -> dict:
    package = await package_collection.find_one({'name': package_name})
    return package

async def update_package_versions(package_id: ObjectId, version_id: ObjectId) -> None:
    await package_collection.find_one_and_update({'_id': package_id}, {'$push': {'versions': version_id}})

async def update_package_moment(package_id: ObjectId) -> None:
    await package_collection.find_one_and_update({'_id': package_id}, {'$set': {'moment': datetime.now()}})