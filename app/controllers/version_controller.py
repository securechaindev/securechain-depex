from bson import ObjectId

from app.services.version_service import update_versions_cves_by_query, read_versions_by_query

from app.utils.get_query import get_complete_query

async def read_versions_by_constraints(constraints: list[list[str]], package_id: ObjectId) -> list:
    query = await get_complete_query(constraints, package_id)
    return await read_versions_by_query(query)

async def update_versions_cves_by_constraints(constraints: list[list[str]], package_id: ObjectId, cve_id: ObjectId) -> None:
    query = await get_complete_query(constraints, package_id)
    await update_versions_cves_by_query(query, cve_id)