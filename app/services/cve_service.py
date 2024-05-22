from typing import Any

from .dbs.databases import get_collection


async def read_cve_by_id(cve_id: str) -> dict[str, Any]:
    cves_collection = get_collection("cves")
    result = await cves_collection.find_one(
        {"id": cve_id},
        {
            "_id": 0,
            "id": 1,
            "description": {"$first": "$descriptions.value"},
            "vuln_impact": {
                "$ifNull": [
                    "$metrics.cvssMetricV31.impactScore",
                    "$metrics.cvssMetricV30.impactScore",
                    "$metrics.cvssMetricV2.impactScore",
                    0.0,
                ]
            },
            "attack_vector": {
                "$ifNull": [
                    "$metrics.cvssMetricV31.cvssData.vectorString",
                    "$metrics.cvssMetricV30.cvssData.vectorString",
                    "$metrics.cvssMetricV2.cvssData.vectorString",
                    "",
                ]
            },
        },
    )
    return result if result is not None else {"vuln_impact": [0.0], "description": {"value": ""}}


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
