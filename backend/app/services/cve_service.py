from typing import Any

from .dbs.databases import get_collection


async def read_cpe_product_by_package_name(package_name: str) -> dict[str, Any]:
    cpe_products_collection = get_collection("cpe_products")
    return await cpe_products_collection.find_one({"product": package_name})
