from typing import Any
from datetime import datetime
from .dbs.databases import get_collection


async def read_env_variables() -> dict[str, Any]:
    env_variable_collection = get_collection('env_variables')
    cursor = env_variable_collection.find()
    for document in await cursor.to_list(length=1):
        return document
    return {}


async def update_env_variables(env_variables_id: str, now: datetime) -> None:
    env_variable_collection = get_collection('env_variables')
    await env_variable_collection.update_one({'_id': env_variables_id}, {'$set': {'last_update': now}})