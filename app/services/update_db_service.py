from typing import Any
from .dbs.databases import get_collection


async def read_env_variables() -> dict[str, Any]:
    env_variable_collection = get_collection('env_variables')
    cursor = env_variable_collection.find()
    for document in await cursor.to_list(length=1):
        return document
    return {}


async def replace_env_variables(env_variables: dict[str, Any]) -> None:
    env_variable_collection = get_collection('env_variables')
    await env_variable_collection.replace_one({'_id': env_variables['_id']}, env_variables)