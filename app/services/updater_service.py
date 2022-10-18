from app.services.dbs.databases import env_variable_collection


async def read_env_variables() -> dict:
    cursor = env_variable_collection.find()
    for document in await cursor.to_list(length = 1):
        return document
    return {}

async def replace_env_variables(env_variables: dict) -> None:
    await env_variable_collection.replace_one({'_id': env_variables['_id']}, {'$set': env_variables})
