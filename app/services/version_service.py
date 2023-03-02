from typing import Any

from bson import ObjectId

from app.utils import get_complete_query

from .dbs.databases import version_collection


async def create_version(version_data: dict[str, Any]) -> dict[str, Any]:
    version = await version_collection.insert_one(version_data)
    new_version = await version_collection.find_one({'_id': version.inserted_id})
    return new_version


async def read_version_by_id(
    version_id: ObjectId,
    fields: dict[str, int] | None = None
) -> dict[str, Any]:
    if not fields:
        fields = {}
    version = await version_collection.find_one({'_id': version_id}, fields)
    return version


async def read_version_by_count_package(
    package: str,
    count: float | int,
    fields: dict[str, int] | None = None
) -> dict[str, Any]:
    if not fields:
        fields = {}
    version = await version_collection.find_one({'package': package, 'count': count}, fields)
    return version


async def get_release_by_count_many(
    configs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    sanitized_configs: list[dict[str, Any]] = []
    for config in configs:
        sanitized_config: dict[str, Any] = {}
        for var, value in config.items():
            version = await read_version_by_count_package(var, value)
            if version:
                sanitized_config[var] = version['release']
            else:
                sanitized_config[var] = value
        sanitized_configs.append(sanitized_config)
    return sanitized_configs


async def get_release_by_count_one(
    config: dict[str, Any]
) -> dict[str, Any]:
    sanitized_config: dict[str, Any] = {}
    for var, value in config.items():
        version = await read_version_by_count_package(var, value)
        if version:
            sanitized_config[var] = version['release']
        else:
            sanitized_config[var] = value
    return sanitized_config


async def get_count_by_release(
    config: dict[str, str]
) -> dict[str, int]:
    sanitized_config: dict[str, int] = {}
    for package, release in config.items():
        version = await read_version_by_release_package(release, package)
        if version:
            sanitized_config[version['package']] = version['count']
    return sanitized_config


async def read_versions_by_constraints(
    constraints: dict[str, str] | str,
    package_name: str
) -> list[dict[str, Any]]:
    query = await get_complete_query(constraints, package_name)
    return [document async for document in version_collection.find(query)]


async def read_versions_ids_by_constraints(
    constraints: dict[str, str] | str,
    package_name: str
) -> list[ObjectId]:
    query = await get_complete_query(constraints, package_name)
    return [document['_id'] async for document in version_collection.find(query, {'_id': 1})]


async def read_version_by_release_package(
    release: str,
    package: str
) -> dict[str, Any]:
    version = await version_collection.find_one(
        {
            'release': release,
            'package': package
        }
    )
    return version


async def update_versions_cves_by_constraints(
    constraints: dict[str, str] | str,
    package_name: str,
    cve: dict[str, Any]
) -> None:
    query = await get_complete_query(constraints, package_name)
    await version_collection.update_many(query, {'$addToSet': {'cves': cve}})


async def update_version_package_edges(
    version_id: ObjectId,
    package_edge_id: ObjectId
) -> None:
    await version_collection.find_one_and_update(
        {'_id': version_id},
        {'$push': {'package_edges': package_edge_id}}
    )