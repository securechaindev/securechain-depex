from bson import ObjectId
from app.services.dbs.databases import (depex_package_edge_collection,
                                        pypi_package_edge_collection)


async def select_db(database: str):
    match database:
        case 'depex':
            return depex_package_edge_collection
        case 'pypi':
            return pypi_package_edge_collection


async def create_package_edge(package_edge_data: dict, database: str) -> dict:
    collection = await select_db(database)
    package_edge = await collection.insert_one(package_edge_data)
    new_package_edge = await collection.find_one({'_id': package_edge.inserted_id})
    return new_package_edge


async def read_package_edge_by_id(
    package_edge_id: ObjectId,
    database: str,
    fields: dict = None
) -> dict:
    if not fields:
        fields = {}
    collection = await select_db(database)
    package_edge = await collection.find_one({'_id': package_edge_id}, fields)
    return package_edge


async def read_package_edge_by_name_constraints(
    package_name: str,
    constraints: dict[str, str] | str,
    database: str,
    fields: dict = None
) -> dict:
    if not fields:
        fields = {}
    collection = await select_db(database)
    package_edge = await collection.find_one(
        {'package_name': package_name, 'constraints': constraints},
        fields
    )
    return package_edge


async def update_package_edge(
    package_edge_id: ObjectId,
    package_edge_data: dict,
    database: str
) -> None:
    collection = await select_db(database)
    await collection.replace_one({'_id': package_edge_id}, package_edge_data)