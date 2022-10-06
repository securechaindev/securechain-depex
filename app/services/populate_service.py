from app.services.dbs.databases import (
    cve_collection,
    env_variable_collection
)

from json import load


async def cve_bulkwrite() -> None:
    # Posibilidad de extraer, poblar y borrar de un zip
    export_file = open('app/services/dbs/db_files/cves.json', encoding = 'utf-8')
    json_file = load(export_file)
    cves = json_file['cves']
    env_variables = {
        'last_year_update': json_file['year'],
        'last_month_update': json_file['month'],
        'last_day_update': json_file['day']
    }
    await env_variable_collection.insert_one(env_variables)
    await cve_collection.insert_many(cves)
    await cve_collection.create_index("cve_id")

async def read_env_variables() -> dict:
    cursor = env_variable_collection.find()
    for document in await cursor.to_list(length = 1):
        return document
    return {}

async def update_env_variables(env_variables: dict) -> None:
    await env_variable_collection.find_one_and_update({'_id': env_variables['_id']}, {'$set': env_variables})
