from typing import Any

from .dbs.databases import cve_collection


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
                'impact_score': {
                    '$ifNull': ['$metrics.cvssMetricV31.impactScore', 
                                '$metrics.cvssMetricV30.impactScore', 
                                '$metrics.cvssMetricV2.impactScore', 
                                0.]
                },
                'configurations.nodes.cpeMatch': 1,
                'products': 1
            }
        },
        {
            '$match': {
                'products': {'$in': [package_name]}
            }
        }
    ]
    try:
        return [cpe_match async for cpe_match in cve_collection.aggregate(pipeline)]
    except:
        return []