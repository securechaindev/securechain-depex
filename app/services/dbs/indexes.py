from app.services.dbs.databases import get_collection, get_graph_db_session


async def create_indexes() -> None:
    smt_text_collection = get_collection("smt_text")
    cves_collection = get_collection("cves")
    cpe_matchs_collection = get_collection("cpe_matchs")
    cpes_collection = get_collection("cpes")
    cpe_products_collection = get_collection("cpe_products")
    cwes_collection = get_collection("cwes")
    exploits_collection = get_collection("exploits")
    await smt_text_collection.create_index("smt_id", unique=True)
    await cves_collection.create_index("id", unique=True)
    await cpe_matchs_collection.create_index("matchCriteriaId", unique=True)
    await cpes_collection.create_index("cpeNameId", unique=True)
    await cpe_products_collection.create_index("product", unique=True)
    await cwes_collection.create_index("@ID", unique=True)
    await cwes_collection.create_index("cvelist", unique=False)
    await exploits_collection.create_index("id", unique=True)
    await exploits_collection.create_index("cvelist", unique=False)
    for session in get_graph_db_session("ALL"):
        await session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE"
        )
