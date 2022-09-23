from bson import ObjectId

from app.services.dbs.databases import depex_package_edge_collection, pypi_package_edge_collection


async def create_package_edge(package_edge_data: dict, db: str) -> dict:
    match db:
        case 'depex':
            collection = depex_package_edge_collection
        case 'pypi':
            collection = pypi_package_edge_collection

    package_edge = await collection.insert_one(package_edge_data)
    new_package_edge = await collection.find_one({'_id': package_edge.inserted_id})
    return new_package_edge

async def update_package_edge_versions(package_edge_id: ObjectId, versions: list, db: str) -> dict:
    match db:
        case 'depex':
            collection = depex_package_edge_collection
        case 'pypi':
            collection = pypi_package_edge_collection

    updated_package_edge = await collection.find_one_and_update({'_id': package_edge_id}, {'$set': {'versions': versions}})
    return updated_package_edge