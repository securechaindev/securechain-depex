# mypy: ignore-errors
from typing import Any
from .dbs.databases import get_collection


async def read_cve_impact_by_id(cve_id: str) -> dict[str, list[str]]:
    cves_collection = get_collection('cves')
    return await cves_collection.find_one(
        {
            'id': cve_id
        },
        {
            '_id': 0, 
            'impact_score': {
                '$ifNull': ['$metrics.cvssMetricV31.impactScore', 
                            '$metrics.cvssMetricV30.impactScore', 
                            '$metrics.cvssMetricV2.impactScore', 
                            0.]
            }
        }
    )


async def read_cpe_matches_by_package_name(package_name: str) -> list[dict[str, Any]]:
    cves_collection = get_collection('cves')
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
        return [cpe_match async for cpe_match in cves_collection.aggregate(pipeline)]
    except:
        return []