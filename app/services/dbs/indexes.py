from app.services.dbs.databases import get_graph_db_session, get_collection


async def create_indexes() -> None:
    cve_collection = get_collection('cves')
    exploits_collection = get_collection('exploits')
    await cve_collection.create_index('id', unique=True)
    await cve_collection.create_index('products', unique=False)
    await exploits_collection.create_index('cves', unique=False)
    pypi_session = get_graph_db_session('PIP')
    npm_session = get_graph_db_session('NPM')
    mvn_session = get_graph_db_session('MVN')
    for session in [pypi_session, mvn_session, npm_session]:
        await session.run(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE'
        )
        await session.run(
            'CREATE TEXT INDEX IF NOT EXISTS FOR (p: Package) ON (p.name)'
        )