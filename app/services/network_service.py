from bson import ObjectId
from fastapi import HTTPException

from app.services.dbs.databases import network_collection


async def create_network(network_data: dict) -> dict:
    network = await network_collection.insert_one(network_data)
    new_network = await network_collection.find_one({'_id': network.inserted_id})
    return new_network

async def read_network_by_id(network_id: str, fields: dict = {}) -> dict:
    network = await network_collection.find_one({'_id': ObjectId(network_id)}, fields)
    if network:
        return network
    raise HTTPException(status_code = 404, detail = [f'Network with id {network_id} not found'])

async def update_network_requirement_files(network_id: ObjectId, requirement_file_id: ObjectId) -> None:
    await network_collection.find_one_and_update({'_id': network_id}, {'$push': {'requirement_files': requirement_file_id}})

async def update_network_is_completed(network_id: ObjectId) -> dict:
    updated_network = await network_collection.find_one_and_update({'_id': network_id}, {'$set': {'is_complete': True}})
    return updated_network