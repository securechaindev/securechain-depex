from bson import ObjectId
from app.services.dbs.databases import (depex_package_edge_collection,
                                        pypi_package_edge_collection)


async def select_db(db: str):
    match db:
        case 'depex':
            return depex_package_edge_collection
        case 'pypi':
            return pypi_package_edge_collection

async def read_package_edge_by_id(package_edge_id: ObjectId, db: str, fields: dict = None) -> dict:
    if not fields: fields = {}
    collection = await select_db(db)
    package_edge = await collection.find_one({'_id': package_edge_id}, fields)
    return package_edge

async def create_package_edge(package_edge_data: dict, db: str) -> dict:
    collection = await select_db(db)
    package_edge = await collection.insert_one(package_edge_data)
    new_package_edge = await collection.find_one({'_id': package_edge.inserted_id})
    return new_package_edge