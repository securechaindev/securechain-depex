from app.services.dbs.databases import get_collection, get_graph_db_driver


async def create_indexes() -> None:
    users_collection = get_collection("users")
    smt_text_collection = get_collection("smt_text")
    cves_collection = get_collection("cves")
    cpe_matchs_collection = get_collection("cpe_matchs")
    cpes_collection = get_collection("cpes")
    cpe_products_collection = get_collection("cpe_products")
    await users_collection.create_index("email", unique=True)
    await smt_text_collection.create_index("smt_id", unique=True)
    await cves_collection.create_index("id", unique=True)
    await cpe_matchs_collection.create_index("matchCriteriaId", unique=True)
    await cpes_collection.create_index("cpeNameId", unique=True)
    await cpe_products_collection.create_index("product", unique=True)
    async with get_graph_db_driver().session() as session:
        await session.run(
            "create constraint unique_user_name if not exists for (u:User) require u._id is unique"
        )
        await session.run(
            "create constraint unique_repository if not exists for (r:Repository) require (r.owner, r.name) is unique"
        )
        await session.run(
            "create constraint unique_package if not exists for (p:Package) require (p.manager, p.group_id, p.name) is unique"
        )
