from typing import Any

from .dbs.databases import get_graph_db_session


async def create_requirement_file(requirement_file: dict[str, Any], repository_id: str, package_manager: str) -> str:
    query = '''
    match (r:Repository)
    where elementid(r) = $repository_id
    create(rf:RequirementFile {name:$name,manager:$manager})
    create (r)-[rel:USE]->(rf)
    return elementid(rf) as id
    '''
    session = get_graph_db_session(package_manager)
    result = await session.run(query, requirement_file, repository_id=repository_id)
    record = await result.single()
    return record[0] if record else None