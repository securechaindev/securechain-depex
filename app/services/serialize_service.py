from typing import Any

from bson import ObjectId
from app.services.dbs.databases import network_collection


async def aggregate_network_by_id(network_id: str) -> dict[str, Any]:
    pipeline = [
        {
            '$match': {
                '_id': ObjectId(network_id)
            }
        },
        {
            '$lookup': {
                'from': 'requirement_files',
                'localField': 'requirement_files',
                'foreignField': '_id',
                'as': 'requirement_files'
            }
        },
        {
            '$unwind': {
                'path': '$requirement_files',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$lookup': {
                'from': 'package_edges',
                'localField': 'requirement_files.package_edges',
                'foreignField': '_id',
                'as': 'requirement_files.package_edges'
            }
        },
        {
            '$group': {
                '_id': '$_id',
                'name': {'$first': '$name'},
                'owner': {'$first': '$owner'},
                'requirement_files': {'$push': '$requirement_files'}
            }
        }
    ]
    async for network in network_collection.aggregate(pipeline):
        return network
    return {}