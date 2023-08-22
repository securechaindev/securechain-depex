from app.services.dbs.databases import get_graph_db_session, get_collection


async def create_indexes() -> None:
    nvd_collection = get_collection('nvd')
    exploit_db_collection = get_collection('exploit_db')
    await nvd_collection.create_index('id', unique=True)
    await nvd_collection.create_index('products', unique=False)
    await exploit_db_collection.create_index('cves', unique=False)
    for session in get_graph_db_session('ALL'):
        await session.run(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE'
        )
        await session.run(
            'CREATE TEXT INDEX IF NOT EXISTS FOR (p: Package) ON (p.name)'
        )