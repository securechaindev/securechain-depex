from app.services.dbs.databases import cve_collection


async def create_cve(cve_data: dict) -> dict:
    cve = await cve_collection.insert_one(cve_data)
    new_cve = await cve_collection.find_one({'_id': cve.inserted_id})
    return new_cve

async def read_cve_by_cve_id(cve_id: str) -> dict:
    cve = await cve_collection.find_one({'id': cve_id})
    return cve

async def bulk_write_cve_actions(actions: list) -> None:
    await cve_collection.bulk_write(actions, ordered = True)

async def read_cpe_matches_by_package_name(package_name: str) -> list:
    pipeline = [
        {'$project': {'configurations.nodes.cpeMatch': 1}},
        {'$unwind': '$configurations'},
        {'$unwind': '$configurations.nodes'},
        {'$unwind': '$configurations.nodes.cpeMatch'},
        {
            '$match': {
                'configurations.nodes.cpeMatch.criteria': {
                    '$regex': package_name
                }
            }
        }
    ]
    return [cpe_match async for cpe_match in cve_collection.aggregate(pipeline)]