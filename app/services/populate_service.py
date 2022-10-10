from app.services.dbs.databases import (
    cve_collection,
    env_variable_collection
)

from app.utils.get_zip_data import get_zip_data


async def cve_bulkwrite() -> None:
    json_file = await get_zip_data()
    env_variables = {
        'last_year_update': json_file['year'],
        'last_month_update': json_file['month'],
        'last_day_update': json_file['day']
    }
    await env_variable_collection.insert_one(env_variables)
    await cve_collection.insert_many(json_file['cves'])
    await cve_collection.create_index("id", unique = True)

async def read_env_variables() -> dict:
    cursor = env_variable_collection.find()
    for document in await cursor.to_list(length = 1):
        return document
    return {}

async def replace_env_variables(env_variables: dict) -> None:
    await env_variable_collection.replace_one({'_id': env_variables['_id']}, {'$set': env_variables})
