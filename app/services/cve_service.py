from typing import Any

from bson import ObjectId
from app.services import cve_collection


async def create_cve(cve_data: dict[str, Any]) -> dict[str, Any]:
    cve = await cve_collection.insert_one(cve_data)
    new_cve = await cve_collection.find_one({'_id': cve.inserted_id})
    return new_cve


async def read_cve_by_id(cve_id: ObjectId, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    if not fields:
        fields = {}
    cve = await cve_collection.find_one({'_id': cve_id}, fields)
    return cve


async def read_cve_by_cve_id(cve_id: str) -> dict[str, Any] | None:
    cve = await cve_collection.find_one({'id': cve_id})
    return cve


async def bulk_write_cve_actions(actions: list[Any], ordered: bool) -> None:
    await cve_collection.bulk_write(actions, ordered=ordered)


async def read_cpe_matches_by_package_name(package_name: str) -> list[dict[str, Any]]:
    pipeline = [
        {
            '$project': {
                'id': 1,
                'metrics.cvssMetricV2.impactScore': 1,
                'metrics.cvssMetricV30.impactScore': 1,
                'metrics.cvssMetricV31.impactScore': 1,
                'configurations.nodes.cpeMatch': 1
            }
        },
        {'$unwind': '$configurations'},
        {'$unwind': '$configurations.nodes'},
        {'$unwind': '$configurations.nodes.cpeMatch'},
        {
            '$match': {
                'configurations.nodes.cpeMatch.criteria': {
                    '$regex': f':{package_name}:'
                }
            }
        }
    ]
    return [cpe_match async for cpe_match in cve_collection.aggregate(pipeline)]