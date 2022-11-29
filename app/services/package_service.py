from typing import Any

from datetime import datetime

from bson import ObjectId

from app.services.dbs.databases import package_collection


async def create_package(package_data: dict[str, Any]) -> dict[str, Any]:
    package = await package_collection.insert_one(package_data)
    new_package = await package_collection.find_one({'_id': package.inserted_id})
    return new_package


async def read_package_by_id(
    package_id: ObjectId,
    fields: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not fields:
        fields = {}
    package = await package_collection.find_one({'_id': package_id}, fields)
    return package


async def read_package_by_name(package_name: str) -> dict[str, Any] | None:
    package = await package_collection.find_one({'name': package_name})
    return package


async def update_package_versions(package_id: ObjectId, version_id: ObjectId) -> None:
    await package_collection.find_one_and_update(
        {'_id': package_id},
        {'$push': {'versions': version_id}}
    )


async def update_package_moment(package_id: ObjectId) -> None:
    await package_collection.find_one_and_update(
        {'_id': package_id},
        {'$set': {'moment': datetime.now()}}
    )