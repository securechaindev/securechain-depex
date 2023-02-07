from typing import Any

from bson import ObjectId
from app.services import graph_collection


async def aggregate_graph_by_id(graph_id: str) -> dict[str, Any]:
    pipeline = [
        {
            '$match': {
                '_id': ObjectId(graph_id)
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
    async for graph in graph_collection.aggregate(pipeline):
        return graph
    return {}