from typing import Any

from .dbs.databases import get_collection


async def read_cve_impact_by_id(cve_id: str) -> dict[str, list[str]]:
    cves_collection = get_collection("cves")
    return await cves_collection.find_one(
        {"id": cve_id},
        {
            "_id": 0,
            "impact_score": {
                "$ifNull": [
                    "$metrics.cvssMetricV31.impactScore",
                    "$metrics.cvssMetricV30.impactScore",
                    "$metrics.cvssMetricV2.impactScore",
                    .0,
                ]
            },
        },
    )


async def read_cpe_product_by_package_name(package_name: str) -> dict[str, Any]:
    cpe_products_collection = get_collection("cpe_products")
    return await cpe_products_collection.find_one({"product": package_name})


async def update_cpe_products(product: str, cve: dict[str, Any]) -> None:
    cpe_products_collection = get_collection("cpe_products")
    await cpe_products_collection.update_one(
        {"product": product},
        {"$addToSet": {"cves": cve}},
        upsert=True,
    )
