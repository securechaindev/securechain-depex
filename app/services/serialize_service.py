from bson import ObjectId
from app.services.dbs.databases import network_collection, version_collection


async def aggregate_network_by_id(network_id: ObjectId) -> dict:
    pipeline = [
        {
            '$match': {
                '_id': network_id
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

async def aggregate_version_by_id(version_id: ObjectId) -> dict:
    pipeline = [
        {
            '$project': {
                'package_edges': 1
            }
        },
        {
            '$match': {
                '_id': version_id
            }
        },
        {
            '$lookup': {
                'from': 'package_edges',
                'localField': 'package_edges',
                'foreignField': '_id',
                'as': 'package_edges'
            }
        }
    ]
    async for version in version_collection.aggregate(pipeline):
        return version
