from bson import ObjectId

from app.services.dbs.databases import version_collection
from app.utils.get_query import get_complete_query


async def create_version(version_data: dict) -> dict:
    version = await version_collection.insert_one(version_data)
    new_version = await version_collection.find_one({'_id': version.inserted_id})
    return new_version

async def read_version_by_id(version_id: ObjectId, fields: dict = None) -> dict:
    if not fields: fields = {}
    version = await version_collection.find_one({'_id': version_id}, fields)
    return version

async def read_versions_by_constraints(constraints: dict[str, str] | str, package_name: str) -> list:
    query = await get_complete_query(constraints, package_name)
    return [document async for document in version_collection.find(query)]

async def read_versions_ids_by_constraints(constraints: dict[str, str] | str, package_name: str) -> list:
    query = await get_complete_query(constraints, package_name)
    return [document['_id'] async for document in version_collection.find(query, {'_id': 1})]

async def read_version_by_release_and_package(release: str, package_id: ObjectId) -> dict:
    version = await version_collection.find_one({'$and': [{'release': release}, {'package': package_id}]})
    return version

async def update_versions_cves_by_constraints(constraints: dict[str, str] | str, package_name: str, cve: dict) -> None:
    query = await get_complete_query(constraints, package_name)
    await version_collection.update_many(query, {'$addToSet': {'cves': cve}})

async def update_version_package_edges(version_id: ObjectId, package_edge_id: ObjectId) -> None:
    await version_collection.find_one_and_update({'_id': version_id}, {'$push': {'package_edges': package_edge_id}})