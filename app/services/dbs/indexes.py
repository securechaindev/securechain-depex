from pymongo import ASCENDING

from app.services.dbs.databases import cve_collection


async def create_indexes() -> None:
    await cve_collection.create_index('id', unique=True)
    await cve_collection.create_index('products', unique=False)