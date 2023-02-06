from typing import Any

from bson import ObjectId
from fastapi import HTTPException

from app.services.dbs.databases import graph_collection


async def create_graph(graph_data: dict[str, Any]) -> dict[str, Any]:
    graph = await graph_collection.insert_one(graph_data)
    new_graph = await graph_collection.find_one({'_id': graph.inserted_id})
    return new_graph


async def read_graph_by_id(
    graph_id: str,
    fields: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not fields:
        fields = {}
    graph = await graph_collection.find_one({'_id': ObjectId(graph_id)}, fields)
    if graph:
        return graph
    raise HTTPException(status_code=404, detail=[f'Graph with id {graph_id} not found'])


async def update_graph_requirement_files(
    graph_id: ObjectId,
    requirement_file_id: ObjectId
) -> None:
    await graph_collection.find_one_and_update(
        {'_id': graph_id},
        {'$push': {'requirement_files': requirement_file_id}}
    )


async def update_graph_is_completed(graph_id: ObjectId) -> dict[str, Any]:
    updated_graph = await graph_collection.find_one_and_update(
        {'_id': graph_id},
        {'$set': {'is_complete': True}}
    )
    return updated_graph